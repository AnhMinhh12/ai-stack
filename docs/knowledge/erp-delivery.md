# Lệnh giao hàng (TO2)

## Nguồn và dữ liệu
Dữ liệu lệnh giao hàng lưu tại `public.ph96` với mã chứng từ TO2.
- `status`: mã trạng thái chứng từ (ví dụ: status=1 là "Chờ chỉ thị lô").
- `statusname`: tên trạng thái nghiệp vụ đối chiếu từ `sys_dmtt`.
- `date0`, `time0`: thời điểm lập/tạo chứng từ.

## Quy tắc nghiệp vụ
Khi người dùng hỏi lệnh giao hàng hoàn thiện khi nào, tra cứu trạng thái `status` và `statusname` của lệnh. Nếu lệnh đang ở trạng thái chưa hoàn thành (như "Chờ chỉ thị lô"), phải báo rõ trạng thái hiện tại và thời điểm tạo, không tự coi ngày tạo là ngày hoàn tất.
