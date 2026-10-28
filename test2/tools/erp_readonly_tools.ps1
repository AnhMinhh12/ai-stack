<#
.SYNOPSIS
    ERP Read-Only Discovery & Evidence Collector Tool
.DESCRIPTION
    A structured, audited, read-only toolset to collect ERP menu trees,
    grid column metadata, and redacted schemas without executing any write operations.
.NOTES
    Safety: Zero write operations (no Add, Edit, Delete, Approve, Post, Import).
#>

[CmdletBinding()]
param(
    [string]$BaseUrl = "http://10.0.6.2:1004",
    [string]$Module = "ERP",
    [string]$Unit = "001",
    [string]$Lang = "vi-VN"
)

function Test-ErpConnectivity {
    [CmdletBinding()]
    param(
        [string]$HostName = "10.0.6.2",
        [int]$Port = 1004
    )
    Write-Host "[*] Checking TCP connectivity to $HostName : $Port..." -ForegroundColor Cyan
    $tcp = Test-NetConnection -ComputerName $HostName -Port $Port
    if ($tcp.TcpTestSucceeded) {
        Write-Host "[+] TCP Port $Port is OPEN on $HostName." -ForegroundColor Green
    } else {
        Write-Warning "[-] TCP Port $Port is CLOSED or unreachable on $HostName."
    }
    return $tcp.TcpTestSucceeded
}

function Get-ErpAuthSession {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$UserName,
        [Parameter(Mandatory=$true)]
        [System.Security.SecureString]$PasswordSecure,
        [string]$MaDvcs = "001",
        [string]$Language = "vi-VN"
    )
    $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($PasswordSecure)
    $plainPass = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($bstr)
    [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)

    $body = @{
        user_name = $UserName
        pass = $plainPass
        ma_dvcs = $MaDvcs
        languages = $Language
    } | ConvertTo-Json

    $headers = @{
        "user_name" = $UserName
        "module" = "ERP"
    }

    $loginUrl = "$BaseUrl/SysAPI/api/LoginAPI/Check_login/"
    Write-Host "[*] Authenticating with $loginUrl..." -ForegroundColor Cyan
    try {
        $raw = Invoke-RestMethod -Uri $loginUrl -Method Post -Body $body -ContentType "application/json" -Headers $headers
        $session = $raw | ConvertFrom-Json
        Write-Host "[+] Authentication successful! User ID: $($session.userinfo.user_id), Name: $($session.userinfo.ten)" -ForegroundColor Green
        return $session
    } catch {
        Write-Error "[-] Authentication failed: $_"
        return $null
    }
}

function Get-ErpGridColumns {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory=$true)]
        [string]$GridId,
        [Parameter(Mandatory=$true)]
        [hashtable]$AuthHeaders
    )
    $url = "$BaseUrl/ConfigAPI/api/LookUp/LookUpConfigAPI/InitGridMenu/?gridid=$GridId&form_trans=%23"
    try {
        $res = Invoke-RestMethod -Uri $url -Method Get -Headers $AuthHeaders -TimeoutSec 5
        if ($res.Result -and $res.Result.grid -and $res.Result.grid.Count -gt 0) {
            return $res.Result.grid[0].header
        }
        return @()
    } catch {
        Write-Warning "Failed to query grid for $GridId: $_"
        return @()
    }
}

Export-ModuleMember -Function Test-ErpConnectivity, Get-ErpAuthSession, Get-ErpGridColumns -ErrorAction SilentlyContinue
