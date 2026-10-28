<#
.SYNOPSIS
  Batch scans every accessible ERP menu screen using read-only HTTP requests.
.DESCRIPTION
  Run this only on Machine B, which can reach ERP Web. It logs in only when a
  token is not supplied, fetches the menu, captures InitGridMenu metadata for
  every leaf, and attempts the conventional GET data endpoint for V/V1 voucher
  screens. It never calls Save, Approve, Delete, Post, Import or other writes.
  Failed/unknown endpoints are recorded for discovery; they are not guessed as
  successful mappings.
#>
[CmdletBinding()]
param(
  [string]$BaseUrl = 'http://10.0.6.2:1004',
  [string]$OutputRoot = (Join-Path $PSScriptRoot '..'),
  [string]$UserName,
  [string]$Token,
  [int]$UserId = 0,
  [string]$Unit = '001',
  [string]$Language = 'vi-VN',
  [int]$PageSize = 20
)

$ErrorActionPreference = 'Stop'
$OutputRoot = (Resolve-Path $OutputRoot).Path
$evidenceConfig = Join-Path $OutputRoot 'evidence/config'
$evidenceData = Join-Path $OutputRoot 'evidence/data-api'
$handoff = Join-Path $OutputRoot 'handoff'
New-Item -ItemType Directory -Force -Path $evidenceConfig,$evidenceData,$handoff | Out-Null

function Convert-SecureStringToPlainText([Security.SecureString]$Value) {
  $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($Value)
  try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr) }
  finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr) }
}

if (-not $Token) {
  if (-not $UserName) { $UserName = Read-Host 'ERP user name' }
  $securePassword = Read-Host 'ERP password' -AsSecureString
  $plainPassword = Convert-SecureStringToPlainText $securePassword
  try {
    $loginHeaders = @{ user_name = $UserName; module = 'ERP' }
    $loginBody = @{ user_name=$UserName; pass=$plainPassword; ma_dvcs=$Unit; languages=$Language } | ConvertTo-Json -Compress
    $session = Invoke-RestMethod -Uri "$BaseUrl/SysAPI/api/LoginAPI/Check_login/" -Method Post -Headers $loginHeaders -ContentType 'application/json' -Body $loginBody
  } finally {
    $plainPassword = $null
  }
  $Token = $session.token
  $UserId = [int]$session.userinfo.user_id
  if (-not $Token -or $UserId -le 0) { throw 'Login did not return a usable token and user ID.' }
}
if (-not $UserName) { throw 'Provide -UserName when supplying -Token.' }
if ($UserId -le 0) { throw 'Provide -UserId when supplying -Token.' }

$headers = @{ Token=$Token; user_name=$UserName; user_id="$UserId"; lang=$Language; ma_dvcs=$Unit; module='ERP'; application='ERP'; FROM='web' }
$menuUrl = "$BaseUrl/SysAPI/api/LoginAPI/GetTree_Module/?user_id=$UserId&module=ERP"
$menu = Invoke-RestMethod -Uri $menuUrl -Method Get -Headers $headers
$menu | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 (Join-Path $handoff 'menu-tree-batch.json')
$leafs = @($menu | Where-Object { $_.isleaf -eq $true })
$results = [Collections.Generic.List[object]]::new()

foreach ($screen in $leafs) {
  $state = if ($screen.state) { [string]$screen.state } else { [string]$screen.text }
  $module = if ($screen.module) { [string]$screen.module } else { 'ERP' }
  $screenType = if ($screen.type) { [string]$screen.type } else { '' }
  $configStatus = 'NOT_ATTEMPTED'; $configHttp = ''; $dataStatus = 'NOT_ATTEMPTED'; $dataEndpoint = ''
  $configPath = Join-Path $evidenceConfig "$state.json"

  if ($screenType -eq 'GDB') {
    $configStatus = 'GRAFANA_EMBED'; $configHttp = 'N/A'; $dataStatus = 'NEEDS_GRAFANA_PANEL_DISCOVERY'
    [pscustomobject]@{screen_state=$state; type='GDB'; option_ext=$screen.option_ext} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $configPath
  } elseif ($screen.url -eq '#' -or [string]::IsNullOrWhiteSpace($screen.url)) {
    $configStatus = 'SPECIAL_PAGE'; $configHttp = 'N/A'; $dataStatus = 'NEEDS_UI_BEHAVIOR_DISCOVERY'
    [pscustomobject]@{screen_state=$state; url=$screen.url; template_url=$screen.templateUrl; type=$screenType} | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 $configPath
  } else {
    try {
      $configUrl = "$BaseUrl/ConfigAPI/api/LookUp/LookUpConfigAPI/InitGridMenu/?gridid=$([uri]::EscapeDataString($state))&form_trans=%23"
      $response = Invoke-WebRequest -Uri $configUrl -Method Get -Headers $headers -TimeoutSec 12
      $configHttp = [string]$response.StatusCode
      $config = $response.Content | ConvertFrom-Json
      $columns = @($config.Result.grid[0].header).Count
      $configStatus = if ($columns -gt 0) { 'CONFIG_FOUND' } else { 'NO_GRID_CONFIG' }
      [pscustomobject]@{screen_state=$state; http_status=$response.StatusCode; column_count=$columns; response=$config} | ConvertTo-Json -Depth 10 | Set-Content -Encoding UTF8 $configPath
    } catch {
      $configStatus = 'CONFIG_ERROR'; $configHttp = if ($_.Exception.Response) { [string][int]$_.Exception.Response.StatusCode } else { 'NETWORK_OR_TIMEOUT' }
      [pscustomobject]@{screen_state=$state; http_status=$configHttp; error=$_.Exception.Message} | ConvertTo-Json | Set-Content -Encoding UTF8 $configPath
    }

    if ($screenType -in @('V','V1')) {
      $prefix = $state -replace 'Overview$',''
      $dataEndpoint = "/$($module)API/api/Vouchers/$($prefix)API/GetData/"
      $searchDynamic = @{pindex=0; plimit=$PageSize; gridid=$state; stateid=$state; status='*'; pwhere=' 1 = 1 '; user_id=$UserId; cols_search=''} | ConvertTo-Json -Compress
      $dataUrl = "$BaseUrl$dataEndpoint?searchDynamic=$([uri]::EscapeDataString($searchDynamic))"
      try {
        $dataHeaders = @{} + $headers; $dataHeaders.module = $module; $dataHeaders.state = $state
        $dataResponse = Invoke-WebRequest -Uri $dataUrl -Method Get -Headers $dataHeaders -TimeoutSec 20
        $dataStatus = 'DATA_API_CAPTURED'
        [pscustomobject]@{screen_state=$state; endpoint=$dataEndpoint; request=@{method='GET'; searchDynamic=($searchDynamic | ConvertFrom-Json)}; response=($dataResponse.Content | ConvertFrom-Json)} | ConvertTo-Json -Depth 12 | Set-Content -Encoding UTF8 (Join-Path $evidenceData "$state.json")
      } catch {
        $dataStatus = 'DATA_API_ENDPOINT_NEEDS_DISCOVERY'
        [pscustomobject]@{screen_state=$state; endpoint=$dataEndpoint; error=$_.Exception.Message} | ConvertTo-Json | Set-Content -Encoding UTF8 (Join-Path $evidenceData "$state.json")
      }
    } else {
      $dataStatus = 'NEEDS_ENDPOINT_DISCOVERY'
    }
  }
  $results.Add([pscustomobject]@{screen_state=$state; screen_name=$screen.text; module=$module; screen_type=$screenType; config_status=$configStatus; config_http_status=$configHttp; data_endpoint=$dataEndpoint; data_status=$dataStatus})
}

$results | Export-Csv -NoTypeInformation -Encoding UTF8 (Join-Path $handoff 'web-batch-scan.csv')
$results | Group-Object config_status,data_status | Select-Object Name,Count | Format-Table -AutoSize
Write-Host "Completed $($leafs.Count) screens. See handoff/web-batch-scan.csv and evidence/data-api/."
