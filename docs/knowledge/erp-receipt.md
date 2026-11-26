# Bảng kê phiếu nhập kho

## Nguồn và dữ liệu
Dữ liệu nhập kho và điều chuyển lưu tại bảng `public.ct70` với chiều nhập `nxt = 1`.
Người tạo bản ghi lưu tại `userinfo.user_name` qua `user_id0`. Kho xuất điều chuyển lưu tại `src.ma_kho` qua liên kết điều chuyển `stt_rec_dc`.

## Quy tắc nghiệp vụ
Tra dòng phiếu nhập từ `ct70` theo mã và kỳ được yêu cầu. Với câu hỏi “lần gần nhất”, chọn dòng gần nhất trong phạm vi tra cứu.
Người tạo bản ghi (nguoi_nhap) là tài khoản ghi nhận chứng từ trên hệ thống.
