# REL-20260909 — supply-chain scan status

**Status:** `blocked`  
**Reason:** chưa có SBOM, CVE scan, license scan và policy/expiry được ký.

Không ghi `pass` dựa trên việc image có local ID. Trước promotion phải chạy trên đúng final image digest, bao gồm custom Open WebUI sau build:

```text
syft <image>@<digest> -o <approved-format>      # generate SBOM
grype <image>@<digest>                           # CVE scan
<approved-license-scanner> <image>@<digest>      # license policy
```

Mỗi output phải lưu raw result, tool/version, command, exit code, policy version, owner/approver và expiry trong thư mục release evidence. Nếu scanner/parser lỗi, release phải fail closed.
