# Bộ câu hỏi nghiệp vụ mua hàng

Nguồn sự thật:

- Đơn mua và giá mua thực tế: `ph94` + `ct94`.
- Giá mua NCC theo mã hàng, NCC và thời hạn: `dmgiamuact`.
- `dmvt.gia_ton` chỉ là giá tồn/danh mục, không được dùng để trả lời “giá mua”.
- Loại vật tư 41 (BTP) và 51 (TP) là hàng công ty sản xuất, không được chọn làm “mã đã mua”.

## Nhóm lịch sử mua

| Câu hỏi mẫu | Kết quả bắt buộc |
| --- | --- |
| Mã này đã từng mua chưa? | Có/không dựa trên số đơn mua khác nhau |
| Mã này mua bao nhiêu lần? | `so_lan_dat`, tính theo `count(distinct so_ct)` |
| Lần đầu mua khi nào? | `lan_dat_dau_tien` |
| Lần gần nhất mua khi nào? | `lan_dat_gan_nhat` |
| Mua những lần nào? | Ngày, số đơn, NCC, số lượng, ĐVT, tiền tệ, giá và trạng thái từng dòng; trả tối đa 50 dòng |
| Mua bao nhiêu lần và với giá bao nhiêu? | Tổng số lần kèm danh sách từng lần mua/NCC/giá, tối đa 50 dòng |
| Mua của nhà cung cấp nào? | Bảng tổng hợp `ma_kh`, `ten_kh`, số đơn, lần đầu và lần gần nhất từ toàn bộ đơn mua thực tế |

## Nhóm giá mua

| Câu hỏi mẫu | Kết quả bắt buộc |
| --- | --- |
| Giá của mã này là bao nhiêu? | Giá mua gần nhất và tiền tệ; không dùng `gia_ton` |
| Giá mua gần nhất? | `gia_mua_vnd` cùng mã/tên NCC, số đơn và ngày của dòng đơn mua mới nhất |
| Giá thấp nhất/cao nhất? | Min/max trên các dòng có giá lớn hơn 0 |
| Giá trung bình? | Trả cả trung bình đơn giản và bình quân gia quyền theo số lượng |
| Giá các lần mua thay đổi thế nào? | Danh sách theo thời gian, không gộp khác tiền tệ nếu tỷ giá chưa quy đổi |
| Tổng tiền lần mua gần nhất? | `thanh_tien_vnd` và `thanh_tien_nguyen_te` của dòng gần nhất |
| Giá đang áp dụng? | Liệt kê một giá hiệu lực mới nhất cho từng NCC từ `dmgiamuact`; nếu nêu `NCCxxxx` thì chỉ lọc NCC đó |

## Nhóm duyệt giá nhà cung cấp

| Câu hỏi mẫu | Kết quả bắt buộc |
| --- | --- |
| Mã này đã duyệt giá chưa? | `appr_yn` từ `ctbgncc` |
| Báo giá còn hiệu lực không? | `ngay_bd`, `ngay_kt`, `close_yn` |
| Giá duyệt là bao nhiêu? | Giá trước VAT VND/nguyên tệ, thuế suất và trạng thái duyệt |
| Giá trước VAT/sau VAT là bao nhiêu? | Đọc `dmgiamuact` theo mã hàng + NCC + hiệu lực; không thay bằng giá đơn mua lịch sử |
| Cho xem lịch sử duyệt giá | Các bản ghi báo giá mới nhất trước, có số/ngày chứng từ |

## Quy tắc trả lời an toàn

- Không suy ra “đã mua” chỉ vì mã tồn tại trong danh mục.
- Không gọi giá 0 trong danh mục là giá mua.
- Không rút gọn hoặc sửa mã vật tư từ context hội thoại.
- Không tự động thực hiện thao tác duyệt; intent “duyệt giá” hiện chỉ tra trạng thái.
- Không có chứng từ thì trả “chưa tìm thấy trong phạm vi được phép xem”, không khẳng định dữ liệu toàn công ty bằng 0.
