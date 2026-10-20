# Trạng thái kiểm tra chất lượng QC tem

## Nguồn và dữ liệu
Dữ liệu kiểm tra chất lượng tem thành phẩm lưu tại `public.intem_log` (trường `status_qc`) và đối chiếu danh mục `public.sys_listoptions` (form='OQC', form_type='TYPE_ST').
Các mã chuẩn:
- 3: '3 - OK' (Đạt chuẩn)
- 5: '5 - NG' (Hàng lỗi)
- 6: '6 - Chờ xử lý'

## Quy tắc nghiệp vụ
Khi hỏi tồn kho có lot nào đang ở trạng thái khóa hoặc khoanh vùng NG không, tra cứu theo `status_qc`. Nếu toàn bộ tem đều là status_qc = 3 (OK) thì kết luận không có lot nào ở trạng thái khóa hoặc NG.
