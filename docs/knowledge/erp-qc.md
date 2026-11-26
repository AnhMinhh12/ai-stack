# Trạng thái kiểm tra chất lượng QC tem

## Nguồn và dữ liệu
Dữ liệu kiểm tra chất lượng tem thành phẩm lưu tại `public.intem_log` (trường `status_qc`) và đối chiếu danh mục `public.sys_listoptions` (form='OQC', form_type='TYPE_ST').
Các mã chuẩn:
- 3: '3 - OK' (Đạt chuẩn)
- 5: '5 - NG' (Hàng lỗi)
- 6: '6 - Chờ xử lý'

## Quy tắc nghiệp vụ
`status_qc` mô tả kết quả kiểm tra tem trong phạm vi truy vấn. Câu hỏi về lô bị khóa cần nguồn trạng thái khóa lô đã xác minh. Câu hỏi tại một ngày trong quá khứ cần dữ liệu lịch sử tại ngày đó.
