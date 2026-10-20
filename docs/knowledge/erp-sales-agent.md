# Phiếu xuất kho bán hàng — lát cắt agent staging

## Nguồn và hạt dữ liệu
Bảng header public.ph81 và chi tiết public.ct81 nối bằng stt_rec. Mỗi dòng
được nhận diện bằng stt_rec + ln. so_ct là số hiển thị, không phải khóa join.
Nguồn đối soát: docs/erp-screen-mapping.md, mục Bán hàng; manifest
config/erp-reports/bang-ke-phieu-xuat-kho-ban-hang.json và SQL cùng tên.
Lệnh giao hàng ph96/ct96 khác phiếu xuất bán; không dùng thay thế nhau.

## Ngày, trạng thái và số lượng
Lát cắt lọc ngày lập chứng từ ngay_lct, khoảng tối đa 31 ngày, loại ma_gd = 4
như SQL bảng kê hiện tại. Không tự loại trạng thái nháp/hủy: trả status gốc,
chưa đủ căn cứ để gọi số lượng là “đã giao thực tế” hoặc “đã ghi sổ”.
so_luong là số lượng từng dòng trong dvt của dòng; không cộng các đơn vị khác nhau.
Không tuyên bố tổng toàn kỳ nếu has_more=true. Không tự mở rộng ngày khi rỗng.

## Quyền và giới hạn kiểm chứng
Backend yêu cầu grant báo cáo theo user ID đăng nhập, rồi kiểm tra userinfo
và giao của ds_branchs với ds_stocks. Danh sách rỗng bị chặn trừ is_super=1.
Đây là chính sách staging bảo thủ; khác logic cho phép rỗng trong một số handler
cũ. Cần xác nhận ý nghĩa ds_stocks và đối chiếu ERP UI trước khi triển khai.
Trạng thái: pending_ui_validation; chưa xác nhận đủ case UI cho lát cắt này.

## Phạm vi dataset và ranh giới nghiệp vụ
Lát cắt này cung cấp dữ liệu dòng phiếu xuất kho bán hàng (ph81/ct81) qua công cụ query_allowed_records.
Công cụ query_allowed_records chỉ dùng cho dòng xuất bán thực tế theo mã vật tư cụ thể và khoảng ngày.
Đối với các nghiệp vụ khác ngoài xuất bán, sử dụng đúng công cụ chuyên biệt tương ứng:
- Tồn kho sổ sách: dùng query_inventory_balance (cdvt/ct70). Dòng phiếu xuất bán là dòng phát sinh (flow), không phải là số dư tồn kho (stock).
- Bảng giá và MOQ: dùng query_price_list (dmbanggia, dmbanggiact).
- Cấu trúc BOM, loại nhựa: dùng query_bom_structure (mfbom, mfbom_material).
- Hồ sơ khuôn, số shot: dùng query_mold_profile (dmhosokhuon, dmhosokhuonsp).
- Tồn kho theo khuôn/tem: dùng query_mold_label_stock (intem_log).
- Đơn hàng bán (SO): dùng query_sales_orders (ph64, ct64).
- Lịch sử nhập kho: dùng query_receipt_lines (ct70).
- Quy cách đóng gói: dùng query_packaging_spec (dmvt).
- Trạng thái kiểm tra chất lượng tem: dùng query_qc_status (intem_log).
- Giao bù NG: dùng query_replacement_orders (ph96, ct96).
Không suy diễn số liệu từ dòng xuất bán sang các nghiệp vụ trên.
