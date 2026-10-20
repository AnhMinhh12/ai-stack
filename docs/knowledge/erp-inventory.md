# Báo cáo tồn kho sổ sách

## Nguồn và dữ liệu
Tồn kho sổ sách được tính từ tồn đầu kỳ năm trong public.cdvt (ton00) cộng với tổng phát sinh nhập xuất luỹ kế từ đầu năm đến ngày chỉ định trong public.ct70 (sum(sl_nhap - sl_xuat)).
Khi hỏi về số lượng tồn kho sổ sách hiện tại của mã hàng tính đến ngày tham chiếu, BẮT BUỘC gọi công cụ `query_inventory_balance` (cần material, date_as_of). Lấy số lượng tồn từ trường so_luong_ton.

## Quy tắc nghiệp vụ
Tồn kho sổ sách (ledger stock) là số dư tồn tại thời điểm chỉ định (date_as_of).
Dòng phiếu xuất kho bán hàng (sales issues) là dòng luân chuyển (flow), không phải là số lượng tồn kho (stock). Phân biệt rõ giữa tồn kho sổ sách kế toán trong cdvt và tồn kho tem thực tế quét trong intem_log.
