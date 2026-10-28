# UI Test Cases: Sales Order Header (`sales_order_header` / `SO1`)

**Screen**: `Đơn hàng (Hợp đồng)` (`SO1`)  
**URL**: `http://10.0.6.2:1004/Solution/ERP/#/SO/SO1`  
**Captured At**: `2026-10-27T11:00:00+07:00`  
**Role / Unit**: `Admin` (`IT.ERP`, user_id `78`) / `001` (`HTMP QM`)  
**Paging / Total**: 20 rows per page; Server Total: `579,110` records  
**Active Filters**: Default unfiltered list (`status = '*' ; pwhere = ' 1 = 1 '`)

---

## Case 1: Normal Approved Order with PO & Foreign Currency (Duyệt)

*This represents a standard operational sales order that has been reviewed, approved, and linked to a customer PO with foreign currency amounts.*

- **Voucher Number (`so_ct`)**: `001-2606-010007`
- **Internal Record ID (`stt_rec`)**: `A1000000025227547SO1`
- **Document Date (`ngay_ct`)**: `2026-06-24` (Formatted on UI as `24/06/2026`)
- **Transaction Code & Name (`ma_gd` / `ten_gd`)**: `1` / `Đơn hàng -> Lệnh giao hàng`
- **Customer PO Number (`so_po`)**: `HC0H674867000`
- **Customer Code (`ma_kh`)**: `KH0034`
- **Customer Name (`ten_kh`)**: `[REDACTED - CUSTOMER NAME]`
- **Status Code & Label (`status` / `statusname`)**: `2` / `Duyệt`
- **Currency & Exchange Rate (`ma_nt` / `ty_gia`)**: `USD` / `23,080.0`
- **Total Quantity (`t_so_luong`)**: `90.0`
- **Net Amount (`t_tien2`)**: `1,484,928.0`
- **Tax Amount (`t_thue`)**: `0.0`
- **Discount Amount (`t_ck`)**: `0.0`
- **Grand Total Amount (`t_tt`)**: `1,484,928.0`
- **Created By (`user_name0` / `comment0`)**: `SALES1` (`Chu Thị Hồng`) at `2026-06-24 17:44:51`
- **Approved / Updated By (`user_name2` / `comment2`)**: `SALES1` (`Chu Thị Hồng`) at `2026-06-24 17:44:51`
- **Note / Description (`dien_giai`)**: `Đơn hàng import`

---

## Case 2: Unapproved / Pending Draft Order (Chờ duyệt)

*This represents an active newly entered or unapproved sales order awaiting workflow confirmation.*

- **Voucher Number (`so_ct`)**: `001-2609-000001`
- **Internal Record ID (`stt_rec`)**: `A1000000025236420SO1`
- **Document Date (`ngay_ct`)**: `2026-09-07` (Formatted on UI as `07/09/2026`)
- **Transaction Code & Name (`ma_gd` / `ten_gd`)**: `1` / `Đơn hàng -> Lệnh giao hàng`
- **Customer PO Number (`so_po`)**: *(empty)*
- **Customer Code (`ma_kh`)**: `KH0028`
- **Customer Name (`ten_kh`)**: `[REDACTED - CUSTOMER NAME]`
- **Status Code & Label (`status` / `statusname`)**: `1` / `Chờ duyệt`
- **Currency & Exchange Rate (`ma_nt` / `ty_gia`)**: `VND` / `1.0`
- **Total Quantity (`t_so_luong`)**: `1.0`
- **Net Amount (`t_tien2`)**: `0.0`
- **Grand Total Amount (`t_tt`)**: `0.0`
- **Created By (`user_name0` / `comment0`)**: `ITG` (`ITG TECHNOLOGY`) at `2026-09-07 11:29:59`
- **Status Meaning**: `status = 1` denotes pending/unapproved order. Note: System allows pending records to coexist in the overview grid alongside approved records.

---

## Case 3: Replacement / Compensation Order (`ma_gd = 10`) (Giao bù hàng thiếu)

*This directly verifies the critical source assumption: whether replacement orders are distinguished by `ma_gd = 10`.*

- **Voucher Number (`so_ct`)**: `001-2607-000002`
- **Internal Record ID (`stt_rec`)**: `A1000000025235804SO1`
- **Document Date (`ngay_ct`)**: `2026-07-16` (Formatted on UI as `16/07/2026`)
- **Transaction Code & Name (`ma_gd` / `ten_gd`)**: `10` / `Giao bù hàng thiếu`
- **Customer PO Number (`so_po`)**: *(empty)*
- **Customer Code (`ma_kh`)**: `KH0015`
- **Customer Name (`ten_kh`)**: `[REDACTED - CUSTOMER NAME]`
- **Status Code & Label (`status` / `statusname`)**: `2` / `Duyệt`
- **Currency & Exchange Rate (`ma_nt` / `ty_gia`)**: `VND` / `1.0`
- **Total Quantity (`t_so_luong`)**: `10.0`
- **Net Amount (`t_tien2`)**: `0.0`
- **Grand Total Amount (`t_tt`)**: `0.0`
- **Created By (`user_name0` / `comment0`)**: `HTMP` at `2026-07-16 08:16:00`
- **Verification Note**: Confirms `ma_gd = 10` is indeed used by ERP for replacement deliveries (`Giao bù hàng thiếu`), while standard orders use `ma_gd = 1` (`Đơn hàng -> Lệnh giao hàng`).
