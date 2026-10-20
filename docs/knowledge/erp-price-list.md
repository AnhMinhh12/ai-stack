# Danh mục bảng giá và MOQ

## Nguồn và dữ liệu
Bảng giá lưu tại public.dmbanggia và chi tiết bảng giá public.dmbanggiact.
Trường sl_min là số lượng đặt tối thiểu (MOQ) được báo giá cho khách hàng.
gia0 là giá trước thuế, gia là giá sau thuế theo đơn vị tiền tệ ma_nt (USD hoặc VND).
Thời hạn hiệu lực từ ngay_bd đến ngay_kt.

## Quy tắc nghiệp vụ
Khi người dùng hỏi MOQ của mã hàng, cần tra cứu sl_min từ bảng giá còn hiệu lực tính đến ngày tham chiếu.
Không lấy số lượng nhỏ nhất trong các phiếu xuất kho làm MOQ.
Bảng giá gắn liền với khách hàng (ma_kh, ten_kh) mua mã hàng đó. Khi cần biết khách hàng mua mã hàng là ai, tra cứu bảng giá theo mã vật tư.
