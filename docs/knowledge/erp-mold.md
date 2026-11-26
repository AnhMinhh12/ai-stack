# Hồ sơ khuôn và tuổi thọ shot

## Nguồn và dữ liệu
Dữ liệu hồ sơ khuôn lưu tại `public.dmhosokhuon` và chi tiết liên kết sản phẩm `public.dmhosokhuonsp`.
- `tong_so_shot`: tổng số shot khuôn đã dập/chạy lũy kế.
- `so_shot_bh`: số shot bảo hành định mức của khuôn.

## Quy tắc nghiệp vụ
Khi hỏi khuôn đã chạy được bao nhiêu shot, tra cứu `tong_so_shot`.
Số shot bảo hành `so_shot_bh` là định mức bảo hành, không đồng nhất với tuổi thọ tối đa hỏng khuôn. Nếu người dùng hỏi ngày dự kiến hết tuổi thọ khuôn theo demand khách hàng, cần báo rõ số shot hiện tại và shot bảo hành, và lưu ý ERP hiện tại chưa có hợp đồng tính toán tự động ngày kết thúc tuổi thọ khuôn.
