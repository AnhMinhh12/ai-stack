# Bảng kê phiếu nhập kho

## Nguồn và dữ liệu
Dữ liệu nhập kho và điều chuyển lưu tại bảng `public.ct70` với chiều nhập `nxt = 1`.
Người tạo bản ghi lưu tại `userinfo.user_name` qua `user_id0`. Kho xuất điều chuyển lưu tại `src.ma_kho` qua liên kết điều chuyển `stt_rec_dc`.

## Quy tắc nghiệp vụ
Khi người dùng hỏi về thời điểm nhập kho, số lượng nhập, kho xuất sang hoặc người nhập, tra cứu dòng phiếu nhập gần nhất từ `ct70`.
Người tạo bản ghi (nguoi_nhap) là tài khoản ghi nhận chứng từ trên hệ thống.
