# FreeCAD MCP qua Tailscale — trạng thái vận hành local

**Cập nhật:** 2026-09-25  
**Trạng thái:** `operator-confirmed; repository-unmanaged`

## Điều đã xác nhận

- FreeCAD chạy trên máy local của người dùng, không chạy trong Docker stack tại
  `/home/admin/ai-stack`.
- Một MCP bridge đã được kết nối để Open WebUI/agent có thể gọi FreeCAD.
- Kết nối bridge đi qua Tailscale. Đây là đường private-network, không phải endpoint
  Internet công cộng.

Các thông tin trên được xác nhận bởi operator trong phiên vận hành. Repository không
chứa bridge source/configuration, địa chỉ tailnet, identity, phiên bản FreeCAD, tool
schema, log hoặc evidence test. Không suy diễn các chi tiết đó là đã được kiểm chứng.

## Luồng và ranh giới trách nhiệm

```text
Người dùng → Nginx/Open WebUI (GB10) → MCP bridge qua Tailscale → FreeCAD local → FCStd/STEP
```

Open WebUI chỉ có thể gọi FreeCAD nếu tool MCP được gán cho model/profile hoặc chat
đang dùng. Một chat mới hay model khác có thể không kế thừa tool selection. Khi model
chỉ viết hướng dẫn thay vì gọi tool, kiểm tra tool attachment/capability trước khi kết
luận bridge hay Tailscale lỗi.

## Quy trình kiểm tra tối thiểu

1. Trong chat dùng đúng model/profile có FreeCAD MCP, yêu cầu model liệt kê tool CAD
   khả dụng hoặc tạo document thử không phá hủy.
2. Xác nhận bridge online trong UI/log bridge và Tailscale peer reachable; không đưa
   endpoint hay key vào chat, repo hoặc evidence.
3. Xác nhận FreeCAD nhận lệnh, tạo một document có tên test, lưu vào thư mục đã phê
   duyệt và có thể mở lại.
4. Nếu chat bị mất, tạo chat mới và gán lại tool; không dùng kết quả chat trước làm
   bằng chứng còn quyền điều khiển CAD.

## Control bắt buộc trước khi dùng rộng rãi

- Tailnet ACL chỉ cho phép host Open WebUI/bridge và máy FreeCAD cần thiết; không mở
  port bridge ra LAN/Internet công cộng.
- Xác thực bridge độc lập, secret lưu ngoài repo; xoay/revoke được và không dùng chung
  với `VLLM_API_KEY`.
- Allowlist tool ở mức cần thiết; chặn shell tùy ý, path traversal, đọc/ghi ngoài thư
  mục CAD được phê duyệt và macro không tin cậy.
- Mọi thao tác tạo/sửa/xuất/xóa phải có actor, thời gian, document/path, tool/action,
  outcome và correlation ID; không log prompt hoặc secret.
- Đặt owner, backup/retention cho `.FCStd`, export `.STEP`/bản phát hành, và diễn tập
  khôi phục một file mẫu. File CAD local hiện không nằm trong backup script của repo.
- Test các trạng thái bridge offline, Tailnet denied, FreeCAD busy/crash, tool timeout,
  save/export fail và reconnect. Tool có side effect không được tự retry mù quáng.

## Giới hạn hiện tại

Tích hợp local phù hợp pilot một người/ít người. Nó không phải service HA: máy FreeCAD,
GUI session, bridge và kết nối Tailscale đều là single points of failure. Chưa được
phép mô tả là production-ready hay dùng cho nhiều người cho đến khi có owner, ACL,
observability, backup và evidence riêng.
