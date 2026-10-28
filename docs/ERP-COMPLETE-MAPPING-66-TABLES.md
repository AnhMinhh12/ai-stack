# Danh mục ánh xạ toàn bộ 66 bảng tra cứu ERP/MES với Database

> Bản đặc tả kỹ thuật và ánh xạ vật lý phục vụ tra cứu nội bộ bằng AI trên Open WebUI.
> Dữ liệu nguồn: PostgreSQL `3SERP_HTMP_DATA` (Host `10.0.6.2:5410`, User `read_htmp`).

## 1. Tổng quan phân bổ theo phân hệ

| Phân hệ | Số lượng bảng | Nguồn dữ liệu cốt lõi | Trạng thái kỹ thuật |
| :--- | :---: | :--- | :--- |
| **Bán hàng (Sales / SO)** | 12 | `ph64/ct64`, `ph96/ct96`, `ph81/ct81`, `dmkh`, `dmvt` | Đã xác minh catalog & test query |
| **Mua hàng (Purchase / PO)** | 10 | `ph92/ct92`, `ph94/ct94`, `ph91/ct91`, `dmgiamuact` | Đã xác minh catalog |
| **Kho vận (Inventory / IN)** | 14 | `ph71/ct71`, `ph72/ct72`, `ct70`, `cdvt`, `cdvt13` | Đã xác minh catalog & test query |
| **Sản xuất & Kỹ thuật (MF)** | 12 | `mfbom/mfbom_material`, `dmhosokhuon`, `mfrouting` | Đã xác minh catalog & test query |
| **MES (Thực thi xưởng)** | 13 | `mes_oi_dong_thung`, `intem_carton_log`, `mes_oi_bo_shot` | Đã xác minh catalog & test query |
| **Chất lượng (QC)** | 5 | `intem_log.status_qc`, `sys_listoptions`, `qc_*` | Đã xác minh catalog |
| **Tổng cộng** | **66** | **Toàn bộ hệ thống ERP / MES** | **Sẵn sàng tạo View & Intent** |

---

## 2. Chi tiết ánh xạ từng bảng tra cứu

### 1. Đơn hàng (Hợp đồng)
- **Phân hệ**: `Bán hàng`
- **Bảng vật lý trong DB**: `ph64, ct64, dmkh, dmvt`
- **Khóa liên kết / Logic gộp**: `ph64.stt_rec = ct64.stt_rec; ct64.ma_vt = dmvt.ma_vt; ph64.ma_kh = dmkh.ma_kh`
- **Ghi chú nghiệp vụ**: Đơn hàng bán (SO). Header ph64, chi tiết ct64.
- **Số lượng cột trên giao diện**: 20 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 2 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 3 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 4 | Mã giao dịch | `field_root (Mã giao dịch)` | Trực tiếp hoặc format UI |
| 5 | Tên giao dịch | `field_root (Tên giao dịch)` | Trực tiếp hoặc format UI |
| 6 | Số PO KH | `ma_kh / ten_kh` | JOIN dmkh |
| 7 | Mã khách hàng | `ma_kh / ten_kh` | JOIN dmkh |
| 8 | Tên khách hàng | `ma_kh / ten_kh` | JOIN dmkh |
| 9 | Địa chỉ | `field_root (Địa chỉ)` | Trực tiếp hoặc format UI |
| 10 | Người liên lạc | `field_root (Người liên lạc)` | Trực tiếp hoặc format UI |
| 11 | Điện thoại | `field_root (Điện thoại)` | Trực tiếp hoặc format UI |
| 12 | Nhân viên | `field_root (Nhân viên)` | Trực tiếp hoặc format UI |
| 13 | Diễn giải | `field_root (Diễn giải)` | Trực tiếp hoặc format UI |
| 14 | Mã NT | `field_root (Mã NT)` | Trực tiếp hoặc format UI |
| 15 | Tỷ giá | `field_root (Tỷ giá)` | Trực tiếp hoặc format UI |
| 16 | Tổng số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 17 | Tổng tiền | `field_root (Tổng tiền)` | Trực tiếp hoặc format UI |
| 18 | Thuế | `field_root (Thuế)` | Trực tiếp hoặc format UI |
| 19 | Chiết khấu | `ma_kh / ten_kh` | JOIN dmkh |
| 20 | Thanh toán | `field_root (Thanh toán)` | Trực tiếp hoặc format UI |

---

### 2. Lệnh giao hàng
- **Phân hệ**: `Bán hàng`
- **Bảng vật lý trong DB**: `ph96, ct96, dmkh, dmvt`
- **Khóa liên kết / Logic gộp**: `ph96.stt_rec = ct96.stt_rec; ct96.ma_vt = dmvt.ma_vt; ph96.ma_kh = dmkh.ma_kh`
- **Ghi chú nghiệp vụ**: Lệnh giao hàng (DO/TO2). Trạng thái lệnh, ngày giờ giao.
- **Số lượng cột trên giao diện**: 16 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 2 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 3 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 4 | Mã giao dịch | `field_root (Mã giao dịch)` | Trực tiếp hoặc format UI |
| 5 | Ngày GH | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 6 | Giờ GH | `time0 / create_time` | Định dạng HH:mm:ss |
| 7 | Tên giao dịch | `field_root (Tên giao dịch)` | Trực tiếp hoặc format UI |
| 8 | Mã khách hàng | `ma_kh / ten_kh` | JOIN dmkh |
| 9 | Tên khách hàng | `ma_kh / ten_kh` | JOIN dmkh |
| 10 | Địa chỉ | `field_root (Địa chỉ)` | Trực tiếp hoặc format UI |
| 11 | Người liên lạc | `field_root (Người liên lạc)` | Trực tiếp hoặc format UI |
| 12 | Điện thoại | `field_root (Điện thoại)` | Trực tiếp hoặc format UI |
| 13 | Diễn giải | `field_root (Diễn giải)` | Trực tiếp hoặc format UI |
| 14 | Mã NT | `field_root (Mã NT)` | Trực tiếp hoặc format UI |
| 15 | Tỷ giá | `field_root (Tỷ giá)` | Trực tiếp hoặc format UI |
| 16 | Tổng số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |

---

### 3. Phiếu xuất kho bán hàng
- **Phân hệ**: `Bán hàng`
- **Bảng vật lý trong DB**: `ph81, ct81, dmkh, dmvt`
- **Khóa liên kết / Logic gộp**: `ph81.stt_rec = ct81.stt_rec; ct81.ma_vt = dmvt.ma_vt; ph81.ma_kh = dmkh.ma_kh`
- **Ghi chú nghiệp vụ**: Hóa đơn / Phiếu xuất bán hàng (HD1/PXB). Có thuế, chiết khấu, thanh toán.
- **Số lượng cột trên giao diện**: 20 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 2 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 3 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 4 | Mã giao dịch | `field_root (Mã giao dịch)` | Trực tiếp hoặc format UI |
| 5 | Tên giao dịch | `field_root (Tên giao dịch)` | Trực tiếp hoặc format UI |
| 6 | Mã khách hàng | `ma_kh / ten_kh` | JOIN dmkh |
| 7 | Tên khách hàng | `ma_kh / ten_kh` | JOIN dmkh |
| 8 | Địa chỉ | `field_root (Địa chỉ)` | Trực tiếp hoặc format UI |
| 9 | Người liên lạc | `field_root (Người liên lạc)` | Trực tiếp hoặc format UI |
| 10 | Điện thoại | `field_root (Điện thoại)` | Trực tiếp hoặc format UI |
| 11 | Nhân viên | `field_root (Nhân viên)` | Trực tiếp hoặc format UI |
| 12 | Số lệnh giao hàng | `mes_scheduling_code / so_ct` | Trực tiếp |
| 13 | Diễn giải | `field_root (Diễn giải)` | Trực tiếp hoặc format UI |
| 14 | Mã NT | `field_root (Mã NT)` | Trực tiếp hoặc format UI |
| 15 | Tỷ giá | `field_root (Tỷ giá)` | Trực tiếp hoặc format UI |
| 16 | Tổng số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 17 | Tổng tiền | `field_root (Tổng tiền)` | Trực tiếp hoặc format UI |
| 18 | Chiết khấu | `ma_kh / ten_kh` | JOIN dmkh |
| 19 | Thuế | `field_root (Thuế)` | Trực tiếp hoặc format UI |
| 20 | Thanh toán | `field_root (Thanh toán)` | Trực tiếp hoặc format UI |

---

### 4. Bảng kê phiếu xuất kho bán hàng
- **Phân hệ**: `Bán hàng`
- **Bảng vật lý trong DB**: `ph81, ct81, ct70, dmkh, dmvt`
- **Khóa liên kết / Logic gộp**: `ph81.stt_rec = ct81.stt_rec; ct81.stt_rec_nhap = ct70.stt_rec`
- **Ghi chú nghiệp vụ**: Bảng kê chi tiết từng dòng xuất bán theo kho, ngày tạo, người tạo.
- **Số lượng cột trên giao diện**: 23 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Ngày hạch toán | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 3 | Ngày | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 4 | Số chứng từ | `field_root (Số chứng từ)` | Trực tiếp hoặc format UI |
| 5 | Số PO | `field_root (Số PO)` | Trực tiếp hoặc format UI |
| 6 | Mã NT | `field_root (Mã NT)` | Trực tiếp hoặc format UI |
| 7 | Mã KH | `ma_kh / ten_kh` | JOIN dmkh |
| 8 | Tên KH | `ma_kh / ten_kh` | JOIN dmkh |
| 9 | Mã hàng | `ma_vt / product_code` | Trực tiếp |
| 10 | Tên hàng | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 11 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 12 | Số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 13 | Kho hàng | `ma_kh / ten_kh` | JOIN dmkh |
| 14 | Diễn giải | `field_root (Diễn giải)` | Trực tiếp hoặc format UI |
| 15 | Ghi chú | `field_root (Ghi chú)` | Trực tiếp hoặc format UI |
| 16 | Nguồn gốc tạo phiếu (0-Web, 1-Handy, 2-OI) | `field_root (Nguồn gốc tạo phiếu (0-Web, 1-Handy, 2-OI))` | Trực tiếp hoặc format UI |
| 17 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 18 | Ngày tạo | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 19 | Giờ tạo | `time0 / create_time` | Định dạng HH:mm:ss |
| 20 | Người tạo | `field_root (Người tạo)` | Trực tiếp hoặc format UI |
| 21 | Người sửa | `field_root (Người sửa)` | Trực tiếp hoặc format UI |
| 22 | Giờ sửa | `time0 / create_time` | Định dạng HH:mm:ss |
| 23 | Người sửa | `field_root (Người sửa)` | Trực tiếp hoặc format UI |

---

### 5. Bảng kê lệnh giao hàng
- **Phân hệ**: `Bán hàng`
- **Bảng vật lý trong DB**: `ph96, ct96, dmkh, dmvt`
- **Khóa liên kết / Logic gộp**: `ph96.stt_rec = ct96.stt_rec; ct96.ma_vt = dmvt.ma_vt`
- **Ghi chú nghiệp vụ**: Bảng kê chi tiết lệnh giao hàng (DX2/TO2).
- **Số lượng cột trên giao diện**: 25 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 3 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 4 | Mã khách hàng | `ma_kh / ten_kh` | JOIN dmkh |
| 5 | Tên khách hàng | `ma_kh / ten_kh` | JOIN dmkh |
| 6 | Ngày GH | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 7 | Giờ giao | `time0 / create_time` | Định dạng HH:mm:ss |
| 8 | Ngày giao thực tế | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 9 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 10 | Tên vật tư | `field_root (Tên vật tư)` | Trực tiếp hoặc format UI |
| 11 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 12 | Mã kho | `ma_kh / ten_kh` | JOIN dmkh |
| 13 | Số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 14 | Mã lô | `field_root (Mã lô)` | Trực tiếp hoặc format UI |
| 15 | SL đã chỉ thị lô | `so_luong / quantity` | SUM() nếu gộp dòng |
| 16 | Số lượng còn lại | `so_luong / quantity` | SUM() nếu gộp dòng |
| 17 | Diễn giải | `field_root (Diễn giải)` | Trực tiếp hoặc format UI |
| 18 | Ghi chú | `field_root (Ghi chú)` | Trực tiếp hoặc format UI |
| 19 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 20 | Ngày tạo | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 21 | Giờ tạo | `time0 / create_time` | Định dạng HH:mm:ss |
| 22 | Người tạo | `field_root (Người tạo)` | Trực tiếp hoặc format UI |
| 23 | Ngày sửa | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 24 | Giờ sửa | `time0 / create_time` | Định dạng HH:mm:ss |
| 25 | Người sửa | `field_root (Người sửa)` | Trực tiếp hoặc format UI |

---

### 6. Báo cáo tiến độ giao hàng
- **Phân hệ**: `Bán hàng`
- **Bảng vật lý trong DB**: `ph96, ct96, ph81, ct81`
- **Khóa liên kết / Logic gộp**: `ct96.stt_rec = ph96.stt_rec LEFT JOIN ct81 ON ct81.stt_rec_dh = ct96.stt_rec`
- **Ghi chú nghiệp vụ**: So sánh SL theo lệnh giao (ct96) với SL thực tế đã xuất (ct81), tính còn phải giao.
- **Số lượng cột trên giao diện**: 22 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 3 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 4 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 5 | Số PO KH | `ma_kh / ten_kh` | JOIN dmkh |
| 6 | Ngày HĐ | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 7 | Số HĐ | `field_root (Số HĐ)` | Trực tiếp hoặc format UI |
| 8 | Số PO GH | `field_root (Số PO GH)` | Trực tiếp hoặc format UI |
| 9 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 10 | Tên VT | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 11 | Số lượng revise | `so_luong / quantity` | SUM() nếu gộp dòng |
| 12 | Số lượng đơn hàng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 13 | Số lượng lên lệnh | `so_luong / quantity` | SUM() nếu gộp dòng |
| 14 | Số lượng chưa lệnh | `so_luong / quantity` | SUM() nếu gộp dòng |
| 15 | Số lượng đã giao | `so_luong / quantity` | SUM() nếu gộp dòng |
| 16 | SL đóng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 17 | Số lượng còn lại | `so_luong / quantity` | SUM() nếu gộp dòng |
| 18 | Giá bán | `field_root (Giá bán)` | Trực tiếp hoặc format UI |
| 19 | Tiền bán | `field_root (Tiền bán)` | Trực tiếp hoặc format UI |
| 20 | Ngày GH kế hoạch | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 21 | Ngày GH thực tế | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 22 | Tình trạng đơn hàng | `field_root (Tình trạng đơn hàng)` | Trực tiếp hoặc format UI |

---

### 7. Phiếu yêu cầu mua hàng
- **Phân hệ**: `Mua hàng`
- **Bảng vật lý trong DB**: `ph92, ct92, dmvt`
- **Khóa liên kết / Logic gộp**: `ph92.stt_rec = ct92.stt_rec`
- **Ghi chú nghiệp vụ**: Yêu cầu mua hàng nội bộ (PR/PR0).
- **Số lượng cột trên giao diện**: 11 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 2 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 3 | Tên bộ phận | `field_root (Tên bộ phận)` | Trực tiếp hoặc format UI |
| 4 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 5 | Giao dịch | `field_root (Giao dịch)` | Trực tiếp hoặc format UI |
| 6 | Mức độ | `field_root (Mức độ)` | Trực tiếp hoặc format UI |
| 7 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 8 | Mã Nhân viên | `field_root (Mã Nhân viên)` | Trực tiếp hoặc format UI |
| 9 | Tên nhân viên | `field_root (Tên nhân viên)` | Trực tiếp hoặc format UI |
| 10 | Diễn giải | `field_root (Diễn giải)` | Trực tiếp hoặc format UI |
| 11 | Tổng số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |

---

### 8. Đơn hàng mua
- **Phân hệ**: `Mua hàng`
- **Bảng vật lý trong DB**: `ph94, ct94, dmkh, dmvt`
- **Khóa liên kết / Logic gộp**: `ph94.stt_rec = ct94.stt_rec; ph94.ma_kh = dmkh.ma_kh`
- **Ghi chú nghiệp vụ**: Đơn đặt hàng mua NCC (PO/PO1).
- **Số lượng cột trên giao diện**: 20 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 2 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 3 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 4 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 5 | Mã giao dịch | `field_root (Mã giao dịch)` | Trực tiếp hoặc format UI |
| 6 | Tên giao dịch | `field_root (Tên giao dịch)` | Trực tiếp hoặc format UI |
| 7 | Mã NCC | `field_root (Mã NCC)` | Trực tiếp hoặc format UI |
| 8 | Tên NCC | `field_root (Tên NCC)` | Trực tiếp hoặc format UI |
| 9 | Người liên lạc | `field_root (Người liên lạc)` | Trực tiếp hoặc format UI |
| 10 | Điện thoại | `field_root (Điện thoại)` | Trực tiếp hoặc format UI |
| 11 | Địa chỉ | `field_root (Địa chỉ)` | Trực tiếp hoặc format UI |
| 12 | Bộ phận | `field_root (Bộ phận)` | Trực tiếp hoặc format UI |
| 13 | Người phụ trách | `field_root (Người phụ trách)` | Trực tiếp hoặc format UI |
| 14 | Diễn giải | `field_root (Diễn giải)` | Trực tiếp hoặc format UI |
| 15 | Mã NT | `field_root (Mã NT)` | Trực tiếp hoặc format UI |
| 16 | Tỷ giá | `field_root (Tỷ giá)` | Trực tiếp hoặc format UI |
| 17 | Tổng số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 18 | Tổng tiền | `field_root (Tổng tiền)` | Trực tiếp hoặc format UI |
| 19 | Thuế | `field_root (Thuế)` | Trực tiếp hoặc format UI |
| 20 | Thanh toán | `field_root (Thanh toán)` | Trực tiếp hoặc format UI |

---

### 9. Phiếu yêu cầu nhập hàng
- **Phân hệ**: `Mua hàng`
- **Bảng vật lý trong DB**: `ph95, ct95, dmvt`
- **Khóa liên kết / Logic gộp**: `ph95.stt_rec = ct95.stt_rec`
- **Ghi chú nghiệp vụ**: Phiếu yêu cầu nhập hàng mua (YCN).
- **Số lượng cột trên giao diện**: 14 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 3 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 4 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 5 | Mã giao dịch | `field_root (Mã giao dịch)` | Trực tiếp hoặc format UI |
| 6 | Tên giao dịch | `field_root (Tên giao dịch)` | Trực tiếp hoặc format UI |
| 7 | Ngày nhận hàng | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 8 | Tên NCC | `field_root (Tên NCC)` | Trực tiếp hoặc format UI |
| 9 | Người giao hàng | `field_root (Người giao hàng)` | Trực tiếp hoặc format UI |
| 10 | Địa chỉ | `field_root (Địa chỉ)` | Trực tiếp hoặc format UI |
| 11 | Diễn giải | `field_root (Diễn giải)` | Trực tiếp hoặc format UI |
| 12 | Mã NT | `field_root (Mã NT)` | Trực tiếp hoặc format UI |
| 13 | Tỷ giá | `field_root (Tỷ giá)` | Trực tiếp hoặc format UI |
| 14 | Tổng số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |

---

### 10. Phiếu nhập hàng
- **Phân hệ**: `Mua hàng`
- **Bảng vật lý trong DB**: `ph91, ct91, dmkh, dmvt`
- **Khóa liên kết / Logic gộp**: `ph91.stt_rec = ct91.stt_rec`
- **Ghi chú nghiệp vụ**: Phiếu nhập mua hàng vào kho (PNA/PNC).
- **Số lượng cột trên giao diện**: 18 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 3 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 4 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 5 | Ngày HĐ | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 6 | Số HĐ | `field_root (Số HĐ)` | Trực tiếp hoặc format UI |
| 7 | Mã giao dịch | `field_root (Mã giao dịch)` | Trực tiếp hoặc format UI |
| 8 | Tên giao dịch | `field_root (Tên giao dịch)` | Trực tiếp hoặc format UI |
| 9 | Tên NCC | `field_root (Tên NCC)` | Trực tiếp hoặc format UI |
| 10 | Người giao hàng | `field_root (Người giao hàng)` | Trực tiếp hoặc format UI |
| 11 | Địa chỉ | `field_root (Địa chỉ)` | Trực tiếp hoặc format UI |
| 12 | Diễn giải | `field_root (Diễn giải)` | Trực tiếp hoặc format UI |
| 13 | Mã NT | `field_root (Mã NT)` | Trực tiếp hoặc format UI |
| 14 | Tỷ giá | `field_root (Tỷ giá)` | Trực tiếp hoặc format UI |
| 15 | Tổng số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 16 | Tổng tiền | `field_root (Tổng tiền)` | Trực tiếp hoặc format UI |
| 17 | Thuế | `field_root (Thuế)` | Trực tiếp hoặc format UI |
| 18 | Thanh toán | `field_root (Thanh toán)` | Trực tiếp hoặc format UI |

---

### 11. Bảng kê phiếu yêu cầu mua hàng
- **Phân hệ**: `Mua hàng`
- **Bảng vật lý trong DB**: `ph92, ct92, dmvt`
- **Khóa liên kết / Logic gộp**: `ph92.stt_rec = ct92.stt_rec`
- **Ghi chú nghiệp vụ**: Báo cáo bảng kê PR chi tiết theo mã vật tư, phòng ban yêu cầu.
- **Số lượng cột trên giao diện**: 31 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 3 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 4 | Mã bộ phận | `field_root (Mã bộ phận)` | Trực tiếp hoặc format UI |
| 5 | Tên bộ phận | `field_root (Tên bộ phận)` | Trực tiếp hoặc format UI |
| 6 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 7 | Tên vật tư | `field_root (Tên vật tư)` | Trực tiếp hoặc format UI |
| 8 | ĐVT đặt hàng | `field_root (ĐVT đặt hàng)` | Trực tiếp hoặc format UI |
| 9 | Số lượng YC đặt hàng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 10 | Số lượng đã đặt | `so_luong / quantity` | SUM() nếu gộp dòng |
| 11 | Số lượng nhập | `so_luong / quantity` | SUM() nếu gộp dòng |
| 12 | Số lượng đóng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 13 | Số lượng còn lại | `so_luong / quantity` | SUM() nếu gộp dòng |
| 14 | Ngày nhận hàng | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 15 | Ngày về tiêu chuẩn | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 16 | Số ngày chênh lệch | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 17 | Tên NCC | `field_root (Tên NCC)` | Trực tiếp hoặc format UI |
| 18 | Nhóm VT 1 | `field_root (Nhóm VT 1)` | Trực tiếp hoặc format UI |
| 19 | Nhóm VT 2 | `field_root (Nhóm VT 2)` | Trực tiếp hoặc format UI |
| 20 | Nhóm VT 3 | `field_root (Nhóm VT 3)` | Trực tiếp hoặc format UI |
| 21 | Nhóm VT 4 | `field_root (Nhóm VT 4)` | Trực tiếp hoặc format UI |
| 22 | Nhóm VT 5 | `field_root (Nhóm VT 5)` | Trực tiếp hoặc format UI |
| 23 | Nhóm VT 6 (NCC/KH) | `ma_kh / ten_kh` | JOIN dmkh |
| 24 | Nhóm VT 7 | `field_root (Nhóm VT 7)` | Trực tiếp hoặc format UI |
| 25 | Mô tả/Quy cách | `field_root (Mô tả/Quy cách)` | Trực tiếp hoặc format UI |
| 26 | Mục đích sử dụng | `field_root (Mục đích sử dụng)` | Trực tiếp hoặc format UI |
| 27 | Mã kho nhập | `ma_kh / ten_kh` | JOIN dmkh |
| 28 | Loại hình | `field_root (Loại hình)` | Trực tiếp hoặc format UI |
| 29 | Diễn giải | `field_root (Diễn giải)` | Trực tiếp hoặc format UI |
| 30 | Người tạo | `field_root (Người tạo)` | Trực tiếp hoặc format UI |
| 31 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |

---

### 12. Bảng kê đơn hàng mua
- **Phân hệ**: `Mua hàng`
- **Bảng vật lý trong DB**: `ph94, ct94, dmkh, dmvt`
- **Khóa liên kết / Logic gộp**: `ph94.stt_rec = ct94.stt_rec`
- **Ghi chú nghiệp vụ**: Bảng kê PO chi tiết theo NCC, đơn giá, ngày giao hàng dự kiến.
- **Số lượng cột trên giao diện**: 19 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 3 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 4 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 5 | Tên vật tư | `field_root (Tên vật tư)` | Trực tiếp hoặc format UI |
| 6 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 7 | Số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 8 | Mã kho nhập | `ma_kh / ten_kh` | JOIN dmkh |
| 9 | Nhóm VT 1 | `field_root (Nhóm VT 1)` | Trực tiếp hoặc format UI |
| 10 | Nhóm VT 2 | `field_root (Nhóm VT 2)` | Trực tiếp hoặc format UI |
| 11 | Nhóm VT 3 | `field_root (Nhóm VT 3)` | Trực tiếp hoặc format UI |
| 12 | Nhóm VT 4 | `field_root (Nhóm VT 4)` | Trực tiếp hoặc format UI |
| 13 | Nhóm VT 5 | `field_root (Nhóm VT 5)` | Trực tiếp hoặc format UI |
| 14 | Nhóm VT 6 (NCC/KH) | `ma_kh / ten_kh` | JOIN dmkh |
| 15 | Nhóm VT 7 | `field_root (Nhóm VT 7)` | Trực tiếp hoặc format UI |
| 16 | Loại hình | `field_root (Loại hình)` | Trực tiếp hoặc format UI |
| 17 | Diễn giải | `field_root (Diễn giải)` | Trực tiếp hoặc format UI |
| 18 | Người tạo | `field_root (Người tạo)` | Trực tiếp hoặc format UI |
| 19 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |

---

### 13. Bảng kê phiếu yêu cầu nhập hàng
- **Phân hệ**: `Mua hàng`
- **Bảng vật lý trong DB**: `ph95, ct95, dmvt`
- **Khóa liên kết / Logic gộp**: `ph95.stt_rec = ct95.stt_rec`
- **Ghi chú nghiệp vụ**: Bảng kê YCN.
- **Số lượng cột trên giao diện**: 23 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 3 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 4 | Số đơn hàng | `field_root (Số đơn hàng)` | Trực tiếp hoặc format UI |
| 5 | Số phiếu yêu cầu mua | `field_root (Số phiếu yêu cầu mua)` | Trực tiếp hoặc format UI |
| 6 | Ngày nhận hàng | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 7 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 8 | Tên vật tư | `field_root (Tên vật tư)` | Trực tiếp hoặc format UI |
| 9 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 10 | Số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 11 | Mã kho nhập | `ma_kh / ten_kh` | JOIN dmkh |
| 12 | Nhóm VT 1 | `field_root (Nhóm VT 1)` | Trực tiếp hoặc format UI |
| 13 | Nhóm VT 2 | `field_root (Nhóm VT 2)` | Trực tiếp hoặc format UI |
| 14 | Nhóm VT 3 | `field_root (Nhóm VT 3)` | Trực tiếp hoặc format UI |
| 15 | Nhóm VT 4 | `field_root (Nhóm VT 4)` | Trực tiếp hoặc format UI |
| 16 | Nhóm VT 5 | `field_root (Nhóm VT 5)` | Trực tiếp hoặc format UI |
| 17 | Nhóm VT 6 (NCC/KH) | `ma_kh / ten_kh` | JOIN dmkh |
| 18 | Nhóm VT 7 | `field_root (Nhóm VT 7)` | Trực tiếp hoặc format UI |
| 19 | Mã bộ phận | `field_root (Mã bộ phận)` | Trực tiếp hoặc format UI |
| 20 | Tên bộ phận | `field_root (Tên bộ phận)` | Trực tiếp hoặc format UI |
| 21 | Diễn giải | `field_root (Diễn giải)` | Trực tiếp hoặc format UI |
| 22 | User tạo PO | `field_root (User tạo PO)` | Trực tiếp hoặc format UI |
| 23 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |

---

### 14. Bảng kê phiếu nhập hàng
- **Phân hệ**: `Mua hàng`
- **Bảng vật lý trong DB**: `ph91, ct91, dmkh, dmvt`
- **Khóa liên kết / Logic gộp**: `ph91.stt_rec = ct91.stt_rec`
- **Ghi chú nghiệp vụ**: Bảng kê hàng nhập mua theo chứng từ.
- **Số lượng cột trên giao diện**: 33 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 3 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 4 | Số đơn hàng | `field_root (Số đơn hàng)` | Trực tiếp hoặc format UI |
| 5 | Số phiếu yêu cầu | `field_root (Số phiếu yêu cầu)` | Trực tiếp hoặc format UI |
| 6 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 7 | Tên vật tư | `field_root (Tên vật tư)` | Trực tiếp hoặc format UI |
| 8 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 9 | Số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 10 | Mã kho nhập | `ma_kh / ten_kh` | JOIN dmkh |
| 11 | Nhóm VT 1 | `field_root (Nhóm VT 1)` | Trực tiếp hoặc format UI |
| 12 | Nhóm VT 2 | `field_root (Nhóm VT 2)` | Trực tiếp hoặc format UI |
| 13 | Nhóm VT 3 | `field_root (Nhóm VT 3)` | Trực tiếp hoặc format UI |
| 14 | Nhóm VT 4 | `field_root (Nhóm VT 4)` | Trực tiếp hoặc format UI |
| 15 | Nhóm VT 5 | `field_root (Nhóm VT 5)` | Trực tiếp hoặc format UI |
| 16 | Nhóm VT 6 (NCC/KH) | `ma_kh / ten_kh` | JOIN dmkh |
| 17 | Nhóm VT 7 | `field_root (Nhóm VT 7)` | Trực tiếp hoặc format UI |
| 18 | Dạng NX | `field_root (Dạng NX)` | Trực tiếp hoặc format UI |
| 19 | Mã vụ việc | `field_root (Mã vụ việc)` | Trực tiếp hoặc format UI |
| 20 | Tên vụ việc | `field_root (Tên vụ việc)` | Trực tiếp hoặc format UI |
| 21 | Mã phí | `field_root (Mã phí)` | Trực tiếp hoặc format UI |
| 22 | Tên phí | `field_root (Tên phí)` | Trực tiếp hoặc format UI |
| 23 | Diễn giải | `field_root (Diễn giải)` | Trực tiếp hoặc format UI |
| 24 | Mã bộ phận | `field_root (Mã bộ phận)` | Trực tiếp hoặc format UI |
| 25 | Tên BP | `field_root (Tên BP)` | Trực tiếp hoặc format UI |
| 26 | User tạo PO | `field_root (User tạo PO)` | Trực tiếp hoặc format UI |
| 27 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 28 | Tên người tạo | `field_root (Tên người tạo)` | Trực tiếp hoặc format UI |
| 29 | Ngày tạo | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 30 | Giờ tạo | `time0 / create_time` | Định dạng HH:mm:ss |
| 31 | Tên người sửa | `field_root (Tên người sửa)` | Trực tiếp hoặc format UI |
| 32 | Ngày sửa | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 33 | Giờ sửa | `time0 / create_time` | Định dạng HH:mm:ss |

---

### 15. Báo cáo tình trạng đơn hàng mua
- **Phân hệ**: `Mua hàng`
- **Bảng vật lý trong DB**: `ph94, ct94, ct91`
- **Khóa liên kết / Logic gộp**: `ct94.stt_rec = ph94.stt_rec LEFT JOIN ct91 ON ct91.stt_rec_dh = ct94.stt_rec`
- **Ghi chú nghiệp vụ**: Theo dõi PO đã đặt, đã về kho bao nhiêu, còn thiếu bao nhiêu.
- **Số lượng cột trên giao diện**: 33 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 3 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 4 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 5 | Tình trạng | `field_root (Tình trạng)` | Trực tiếp hoặc format UI |
| 6 | Số chứng từ gốc | `field_root (Số chứng từ gốc)` | Trực tiếp hoặc format UI |
| 7 | Số phiếu YC | `field_root (Số phiếu YC)` | Trực tiếp hoặc format UI |
| 8 | Mã NCC | `field_root (Mã NCC)` | Trực tiếp hoặc format UI |
| 9 | Tên NCC | `field_root (Tên NCC)` | Trực tiếp hoặc format UI |
| 10 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 11 | Tên vật tư | `field_root (Tên vật tư)` | Trực tiếp hoặc format UI |
| 12 | Loại hình | `field_root (Loại hình)` | Trực tiếp hoặc format UI |
| 13 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 14 | Nhóm VT 1 | `field_root (Nhóm VT 1)` | Trực tiếp hoặc format UI |
| 15 | Nhóm VT 2 | `field_root (Nhóm VT 2)` | Trực tiếp hoặc format UI |
| 16 | Nhóm VT 3 | `field_root (Nhóm VT 3)` | Trực tiếp hoặc format UI |
| 17 | Nhóm VT 4 | `field_root (Nhóm VT 4)` | Trực tiếp hoặc format UI |
| 18 | Nhóm VT 5 | `field_root (Nhóm VT 5)` | Trực tiếp hoặc format UI |
| 19 | Nhóm VT 6 (NCC/KH) | `ma_kh / ten_kh` | JOIN dmkh |
| 20 | Nhóm VT 7 | `field_root (Nhóm VT 7)` | Trực tiếp hoặc format UI |
| 21 | Số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 22 | Ngày nhận hàng KH | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 23 | Ngày nhận hàng thực | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 24 | Nhanh(chậm) | `field_root (Nhanh(chậm))` | Trực tiếp hoặc format UI |
| 25 | Tình trạng đơn hàng | `field_root (Tình trạng đơn hàng)` | Trực tiếp hoặc format UI |
| 26 | Số CT nhập | `field_root (Số CT nhập)` | Trực tiếp hoặc format UI |
| 27 | SL nhập | `so_luong / quantity` | SUM() nếu gộp dòng |
| 28 | SL đóng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 29 | Còn lại | `field_root (Còn lại)` | Trực tiếp hoặc format UI |
| 30 | Ngày CT HĐ | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 31 | Số CT HĐ | `field_root (Số CT HĐ)` | Trực tiếp hoặc format UI |
| 32 | SL hóa đơn | `so_luong / quantity` | SUM() nếu gộp dòng |
| 33 | Còn lại | `field_root (Còn lại)` | Trực tiếp hoặc format UI |

---

### 16. Báo cáo lịch sử thay đổi giá NCC
- **Phân hệ**: `Mua hàng`
- **Bảng vật lý trong DB**: `dmgiamuact, phbgncc, ctbgncc`
- **Khóa liên kết / Logic gộp**: `dmgiamuact.ma_vt = ct94.ma_vt`
- **Ghi chú nghiệp vụ**: Biến động giá mua NCC qua các kỳ báo giá và đơn mua.
- **Số lượng cột trên giao diện**: 17 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 2 | Tên vật tư | `field_root (Tên vật tư)` | Trực tiếp hoặc format UI |
| 3 | Grade | `field_root (Grade)` | Trực tiếp hoặc format UI |
| 4 | Gốc nhựa | `field_root (Gốc nhựa)` | Trực tiếp hoặc format UI |
| 5 | Tên màu | `field_root (Tên màu)` | Trực tiếp hoặc format UI |
| 6 | Maker | `field_root (Maker)` | Trực tiếp hoặc format UI |
| 7 | Xuất xứ | `field_root (Xuất xứ)` | Trực tiếp hoặc format UI |
| 8 | Chống cháy | `field_root (Chống cháy)` | Trực tiếp hoặc format UI |
| 9 | Brom | `field_root (Brom)` | Trực tiếp hoặc format UI |
| 10 | Nhóm VT 1 | `field_root (Nhóm VT 1)` | Trực tiếp hoặc format UI |
| 11 | Nhóm VT 2 | `field_root (Nhóm VT 2)` | Trực tiếp hoặc format UI |
| 12 | Nhóm VT 3 | `field_root (Nhóm VT 3)` | Trực tiếp hoặc format UI |
| 13 | Nhóm VT 4 | `field_root (Nhóm VT 4)` | Trực tiếp hoặc format UI |
| 14 | Nhóm VT 5 | `field_root (Nhóm VT 5)` | Trực tiếp hoặc format UI |
| 15 | Nhóm VT 6 (NCC/KH) | `ma_kh / ten_kh` | JOIN dmkh |
| 16 | Nhóm VT 7 | `field_root (Nhóm VT 7)` | Trực tiếp hoặc format UI |
| 17 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |

---

### 17. Phiếu xuất kho
- **Phân hệ**: `Kho vận`
- **Bảng vật lý trong DB**: `ph72, ct72, ct70, dmvt`
- **Khóa liên kết / Logic gộp**: `ph72.stt_rec = ct72.stt_rec`
- **Ghi chú nghiệp vụ**: Phiếu xuất kho nội bộ (PXA/PXB).
- **Số lượng cột trên giao diện**: 12 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 3 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 4 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 5 | Mã giao dịch | `field_root (Mã giao dịch)` | Trực tiếp hoặc format UI |
| 6 | Tên giao dịch | `field_root (Tên giao dịch)` | Trực tiếp hoặc format UI |
| 7 | Mã KH | `ma_kh / ten_kh` | JOIN dmkh |
| 8 | Tên khách hàng | `ma_kh / ten_kh` | JOIN dmkh |
| 9 | Kho xuất | `ma_kh / ten_kh` | JOIN dmkh |
| 10 | Loại nhập xuất | `field_root (Loại nhập xuất)` | Trực tiếp hoặc format UI |
| 11 | Tổng số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 12 | Tổng tiền | `field_root (Tổng tiền)` | Trực tiếp hoặc format UI |

---

### 18. Phiếu nhập kho
- **Phân hệ**: `Kho vận`
- **Bảng vật lý trong DB**: `ph74, ct74, ct70, dmvt`
- **Khóa liên kết / Logic gộp**: `ph74.stt_rec = ct74.stt_rec`
- **Ghi chú nghiệp vụ**: Phiếu nhập kho thành phẩm/nguyên vật liệu (PNF/PND).
- **Số lượng cột trên giao diện**: 13 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 3 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 4 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 5 | Mã giao dịch | `field_root (Mã giao dịch)` | Trực tiếp hoặc format UI |
| 6 | Tên giao dịch | `field_root (Tên giao dịch)` | Trực tiếp hoặc format UI |
| 7 | Mã KH | `ma_kh / ten_kh` | JOIN dmkh |
| 8 | Tên khách hàng | `ma_kh / ten_kh` | JOIN dmkh |
| 9 | Kho nhận | `ma_kh / ten_kh` | JOIN dmkh |
| 10 | Loại nhập xuất | `field_root (Loại nhập xuất)` | Trực tiếp hoặc format UI |
| 11 | Tên loại NX | `field_root (Tên loại NX)` | Trực tiếp hoặc format UI |
| 12 | Tổng số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 13 | Tổng tiền | `field_root (Tổng tiền)` | Trực tiếp hoặc format UI |

---

### 19. Phiếu yêu cầu nhập kho
- **Phân hệ**: `Kho vận`
- **Bảng vật lý trong DB**: `ph78, ct78, dmvt`
- **Khóa liên kết / Logic gộp**: `ph78.stt_rec = ct78.stt_rec`
- **Ghi chú nghiệp vụ**: Đề nghị nhập kho (DNV).
- **Số lượng cột trên giao diện**: 10 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 3 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 4 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 5 | Tên giao dịch | `field_root (Tên giao dịch)` | Trực tiếp hoặc format UI |
| 6 | Mã nhân viên | `field_root (Mã nhân viên)` | Trực tiếp hoặc format UI |
| 7 | Tên bộ phận | `field_root (Tên bộ phận)` | Trực tiếp hoặc format UI |
| 8 | Mã bộ phận | `field_root (Mã bộ phận)` | Trực tiếp hoặc format UI |
| 9 | Mã ĐVCS | `field_root (Mã ĐVCS)` | Trực tiếp hoặc format UI |
| 10 | Tổng số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |

---

### 20. Phiếu yêu cầu xuất kho
- **Phân hệ**: `Kho vận`
- **Bảng vật lý trong DB**: `ph77, ct77, dmvt`
- **Khóa liên kết / Logic gộp**: `ph77.stt_rec = ct77.stt_rec`
- **Ghi chú nghiệp vụ**: Đề nghị xuất kho (DXV).
- **Số lượng cột trên giao diện**: 10 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 3 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 4 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 5 | Mã giao dịch | `field_root (Mã giao dịch)` | Trực tiếp hoặc format UI |
| 6 | Tên giao dịch | `field_root (Tên giao dịch)` | Trực tiếp hoặc format UI |
| 7 | Mã nhân viên | `field_root (Mã nhân viên)` | Trực tiếp hoặc format UI |
| 8 | Tên bộ phận | `field_root (Tên bộ phận)` | Trực tiếp hoặc format UI |
| 9 | Mã bộ phận | `field_root (Mã bộ phận)` | Trực tiếp hoặc format UI |
| 10 | Tổng số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |

---

### 21. Danh mục sản phẩm, vật tư
- **Phân hệ**: `Kho vận`
- **Bảng vật lý trong DB**: `dmvt, dmnhomvt, dmthuoctinhvt`
- **Khóa liên kết / Logic gộp**: `dmvt.ma_vt`
- **Ghi chú nghiệp vụ**: Danh mục vật tư: quy cách bao gói, mã thùng, mã khay, packs0.
- **Số lượng cột trên giao diện**: 35 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Mã hàng | `ma_vt / product_code` | Trực tiếp |
| 3 | Tên hàng | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 4 | Tên vật tư 2 | `field_root (Tên vật tư 2)` | Trực tiếp hoặc format UI |
| 5 | Gốc nhựa | `field_root (Gốc nhựa)` | Trực tiếp hoặc format UI |
| 6 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 7 | Loại hàng | `field_root (Loại hàng)` | Trực tiếp hoặc format UI |
| 8 | Nhóm 1 | `field_root (Nhóm 1)` | Trực tiếp hoặc format UI |
| 9 | Nhóm 2 | `field_root (Nhóm 2)` | Trực tiếp hoặc format UI |
| 10 | Nhóm 3 | `field_root (Nhóm 3)` | Trực tiếp hoặc format UI |
| 11 | Nhóm 4 | `field_root (Nhóm 4)` | Trực tiếp hoặc format UI |
| 12 | Nhóm 5 | `field_root (Nhóm 5)` | Trực tiếp hoặc format UI |
| 13 | Nhóm 6 (KH/NCC) | `ma_kh / ten_kh` | JOIN dmkh |
| 14 | Nhóm 7 | `field_root (Nhóm 7)` | Trực tiếp hoặc format UI |
| 15 | Theo dõi tồn kho | `ma_kh / ten_kh` | JOIN dmkh |
| 16 | Nhựa | `field_root (Nhựa)` | Trực tiếp hoặc format UI |
| 17 | Cách tính giá | `field_root (Cách tính giá)` | Trực tiếp hoặc format UI |
| 18 | Quản lý lô | `field_root (Quản lý lô)` | Trực tiếp hoặc format UI |
| 19 | Quản lý serial | `serial_tem_thung / id_carton` | Khóa định danh thùng |
| 20 | Loại hình | `field_root (Loại hình)` | Trực tiếp hoặc format UI |
| 21 | Mã màu | `field_root (Mã màu)` | Trực tiếp hoặc format UI |
| 22 | Mã màu KH | `ma_kh / ten_kh` | JOIN dmkh |
| 23 | Tên màu | `field_root (Tên màu)` | Trực tiếp hoặc format UI |
| 24 | Grade | `field_root (Grade)` | Trực tiếp hoặc format UI |
| 25 | Mã NCC chính | `field_root (Mã NCC chính)` | Trực tiếp hoặc format UI |
| 26 | Tên NCC | `field_root (Tên NCC)` | Trực tiếp hoặc format UI |
| 27 | Mã KH | `ma_kh / ten_kh` | JOIN dmkh |
| 28 | Tên KH | `ma_kh / ten_kh` | JOIN dmkh |
| 29 | TK vật tư | `field_root (TK vật tư)` | Trực tiếp hoặc format UI |
| 30 | TK chênh lệch vật tư | `field_root (TK chênh lệch vật tư)` | Trực tiếp hoặc format UI |
| 31 | TK giá vốn | `field_root (TK giá vốn)` | Trực tiếp hoặc format UI |
| 32 | TK doanh thu | `field_root (TK doanh thu)` | Trực tiếp hoặc format UI |
| 33 | Xuất xứ | `field_root (Xuất xứ)` | Trực tiếp hoặc format UI |
| 34 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 35 | Mẫu in tem | `field_root (Mẫu in tem)` | Trực tiếp hoặc format UI |

---

### 22. Bảng kê phiếu nhập kho
- **Phân hệ**: `Kho vận`
- **Bảng vật lý trong DB**: `ph74, ct74, ct70, dmvt`
- **Khóa liên kết / Logic gộp**: `ct74.stt_rec = ph74.stt_rec`
- **Ghi chú nghiệp vụ**: Bảng kê chi tiết phiếu nhập kho theo mã hàng, kho, ngày.
- **Số lượng cột trên giao diện**: 30 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Ngày | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 3 | Mã CT | `field_root (Mã CT)` | Trực tiếp hoặc format UI |
| 4 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 5 | Mã hàng | `ma_vt / product_code` | Trực tiếp |
| 6 | Tên hàng | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 7 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 8 | Số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 9 | Loại hình | `field_root (Loại hình)` | Trực tiếp hoặc format UI |
| 10 | Mã kho nhập | `ma_kh / ten_kh` | JOIN dmkh |
| 11 | Dạng NX | `field_root (Dạng NX)` | Trực tiếp hoặc format UI |
| 12 | Mã loại NX | `field_root (Mã loại NX)` | Trực tiếp hoặc format UI |
| 13 | Mã vụ việc | `field_root (Mã vụ việc)` | Trực tiếp hoặc format UI |
| 14 | Tên vụ việc | `field_root (Tên vụ việc)` | Trực tiếp hoặc format UI |
| 15 | Mã CP | `field_root (Mã CP)` | Trực tiếp hoặc format UI |
| 16 | Tên CP | `field_root (Tên CP)` | Trực tiếp hoặc format UI |
| 17 | Mã kho xuất | `ma_kh / ten_kh` | JOIN dmkh |
| 18 | Mã BP | `field_root (Mã BP)` | Trực tiếp hoặc format UI |
| 19 | Tên BP | `field_root (Tên BP)` | Trực tiếp hoặc format UI |
| 20 | Mã CĐGT | `field_root (Mã CĐGT)` | Trực tiếp hoặc format UI |
| 21 | Tên CĐGT | `field_root (Tên CĐGT)` | Trực tiếp hoặc format UI |
| 22 | Mã GD | `field_root (Mã GD)` | Trực tiếp hoặc format UI |
| 23 | Tên GD | `field_root (Tên GD)` | Trực tiếp hoặc format UI |
| 24 | Diễn giải | `field_root (Diễn giải)` | Trực tiếp hoặc format UI |
| 25 | Ngày tạo | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 26 | Giờ tạo | `time0 / create_time` | Định dạng HH:mm:ss |
| 27 | Người tạo | `field_root (Người tạo)` | Trực tiếp hoặc format UI |
| 28 | Ngày sửa | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 29 | Giờ sửa | `time0 / create_time` | Định dạng HH:mm:ss |
| 30 | Người sửa | `field_root (Người sửa)` | Trực tiếp hoặc format UI |

---

### 23. Bảng kê phiếu xuất kho
- **Phân hệ**: `Kho vận`
- **Bảng vật lý trong DB**: `ph72, ct72, ct70, dmvt`
- **Khóa liên kết / Logic gộp**: `ct72.stt_rec = ph72.stt_rec`
- **Ghi chú nghiệp vụ**: Bảng kê chi tiết phiếu xuất kho.
- **Số lượng cột trên giao diện**: 31 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 3 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 4 | Mã CT | `field_root (Mã CT)` | Trực tiếp hoặc format UI |
| 5 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 6 | Tên vật tư | `field_root (Tên vật tư)` | Trực tiếp hoặc format UI |
| 7 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 8 | Số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 9 | Loại hình | `field_root (Loại hình)` | Trực tiếp hoặc format UI |
| 10 | Mã kho xuất | `ma_kh / ten_kh` | JOIN dmkh |
| 11 | Mã kho nhập | `ma_kh / ten_kh` | JOIN dmkh |
| 12 | Mã NX | `field_root (Mã NX)` | Trực tiếp hoặc format UI |
| 13 | Mã loại NX | `field_root (Mã loại NX)` | Trực tiếp hoặc format UI |
| 14 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 15 | Mã vụ việc | `field_root (Mã vụ việc)` | Trực tiếp hoặc format UI |
| 16 | Tên vụ việc | `field_root (Tên vụ việc)` | Trực tiếp hoặc format UI |
| 17 | Mã chi phí | `field_root (Mã chi phí)` | Trực tiếp hoặc format UI |
| 18 | Tên chi phí | `field_root (Tên chi phí)` | Trực tiếp hoặc format UI |
| 19 | Mã GD | `field_root (Mã GD)` | Trực tiếp hoặc format UI |
| 20 | Tên GD | `field_root (Tên GD)` | Trực tiếp hoặc format UI |
| 21 | Mã bộ phận | `field_root (Mã bộ phận)` | Trực tiếp hoặc format UI |
| 22 | Tên bộ phận | `field_root (Tên bộ phận)` | Trực tiếp hoặc format UI |
| 23 | Mã CĐGT | `field_root (Mã CĐGT)` | Trực tiếp hoặc format UI |
| 24 | Tên CĐGT | `field_root (Tên CĐGT)` | Trực tiếp hoặc format UI |
| 25 | Diễn giải | `field_root (Diễn giải)` | Trực tiếp hoặc format UI |
| 26 | Ngày tạo | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 27 | Giờ tạo | `time0 / create_time` | Định dạng HH:mm:ss |
| 28 | Người tạo | `field_root (Người tạo)` | Trực tiếp hoặc format UI |
| 29 | Ngày sửa | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 30 | Giờ sửa | `time0 / create_time` | Định dạng HH:mm:ss |
| 31 | Người sửa | `field_root (Người sửa)` | Trực tiếp hoặc format UI |

---

### 24. Bảng kê phiếu nhập, xuất điều chuyển
- **Phân hệ**: `Kho vận`
- **Bảng vật lý trong DB**: `ph75, ct75, ct70, dmvt`
- **Khóa liên kết / Logic gộp**: `ph75.stt_rec = ct75.stt_rec`
- **Ghi chú nghiệp vụ**: Điều chuyển giữa các kho nội bộ (TO1).
- **Số lượng cột trên giao diện**: 25 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 3 | Mã ĐVCS | `field_root (Mã ĐVCS)` | Trực tiếp hoặc format UI |
| 4 | Số lệnh ĐC | `mes_scheduling_code / so_ct` | Trực tiếp |
| 5 | Số phiếu xuất ĐC | `field_root (Số phiếu xuất ĐC)` | Trực tiếp hoặc format UI |
| 6 | Số phiếu nhập ĐC | `field_root (Số phiếu nhập ĐC)` | Trực tiếp hoặc format UI |
| 7 | Mã khách hàng | `ma_kh / ten_kh` | JOIN dmkh |
| 8 | Tên khách hàng | `ma_kh / ten_kh` | JOIN dmkh |
| 9 | Kho xuất | `ma_kh / ten_kh` | JOIN dmkh |
| 10 | Kho nhập | `ma_kh / ten_kh` | JOIN dmkh |
| 11 | Mã vị trí xuất | `field_root (Mã vị trí xuất)` | Trực tiếp hoặc format UI |
| 12 | Mã vị trí nhập | `field_root (Mã vị trí nhập)` | Trực tiếp hoặc format UI |
| 13 | Mã hàng | `ma_vt / product_code` | Trực tiếp |
| 14 | Tên hàng | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 15 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 16 | Số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 17 | Mã GD | `field_root (Mã GD)` | Trực tiếp hoặc format UI |
| 18 | Tên GD | `field_root (Tên GD)` | Trực tiếp hoặc format UI |
| 19 | Diễn giải | `field_root (Diễn giải)` | Trực tiếp hoặc format UI |
| 20 | Ngày tạo | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 21 | Giờ tạo | `time0 / create_time` | Định dạng HH:mm:ss |
| 22 | Người tạo | `field_root (Người tạo)` | Trực tiếp hoặc format UI |
| 23 | Ngày sửa | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 24 | Giờ sửa | `time0 / create_time` | Định dạng HH:mm:ss |
| 25 | Người sửa | `field_root (Người sửa)` | Trực tiếp hoặc format UI |

---

### 25. Bảng kê nhập xuất theo lô
- **Phân hệ**: `Kho vận`
- **Bảng vật lý trong DB**: `ct70, dmvt`
- **Khóa liên kết / Logic gộp**: `ct70.ma_vt = dmvt.ma_vt WHERE nullif(ct70.ma_lo, '') IS NOT NULL`
- **Ghi chú nghiệp vụ**: Bảng kê giao dịch chi tiết theo mã lô.
- **Số lượng cột trên giao diện**: 23 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 3 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 4 | Mã CT | `field_root (Mã CT)` | Trực tiếp hoặc format UI |
| 5 | Mã Khách Hàng/NCC | `ma_kh / ten_kh` | JOIN dmkh |
| 6 | Mã lô | `field_root (Mã lô)` | Trực tiếp hoặc format UI |
| 7 | Mã hàng | `ma_vt / product_code` | Trực tiếp |
| 8 | Mã chuẩn | `field_root (Mã chuẩn)` | Trực tiếp hoặc format UI |
| 9 | Tên hàng | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 10 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 11 | Mã kho nhập | `ma_kh / ten_kh` | JOIN dmkh |
| 12 | Mã kho xuất | `ma_kh / ten_kh` | JOIN dmkh |
| 13 | Số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 14 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 15 | Loại nhập xuất | `field_root (Loại nhập xuất)` | Trực tiếp hoặc format UI |
| 16 | Mã GD | `field_root (Mã GD)` | Trực tiếp hoặc format UI |
| 17 | Tên GD | `field_root (Tên GD)` | Trực tiếp hoặc format UI |
| 18 | Ngày tạo | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 19 | Giờ tạo | `time0 / create_time` | Định dạng HH:mm:ss |
| 20 | Người tạo | `field_root (Người tạo)` | Trực tiếp hoặc format UI |
| 21 | Ngày sửa | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 22 | Giờ sửa | `time0 / create_time` | Định dạng HH:mm:ss |
| 23 | Người sửa | `field_root (Người sửa)` | Trực tiếp hoặc format UI |

---

### 26. Báo cáo tồn kho
- **Phân hệ**: `Kho vận`
- **Bảng vật lý trong DB**: `ct70, dmvt`
- **Khóa liên kết / Logic gộp**: `SELECT ma_vt, sum(sl_nhap) - sum(sl_xuat) AS ton FROM ct70 GROUP BY ma_vt`
- **Ghi chú nghiệp vụ**: Tồn kho tổng hợp toàn công ty.
- **Số lượng cột trên giao diện**: 7 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 3 | Tên vật tư | `field_root (Tên vật tư)` | Trực tiếp hoặc format UI |
| 4 | Tên vật tư 2 | `field_root (Tên vật tư 2)` | Trực tiếp hoặc format UI |
| 5 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 6 | Nhóm VT 6 (KH/NCC) | `ma_kh / ten_kh` | JOIN dmkh |
| 7 | Số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |

---

### 27. Báo cáo tồn theo kho
- **Phân hệ**: `Kho vận`
- **Bảng vật lý trong DB**: `ct70, dmvt, dmkho`
- **Khóa liên kết / Logic gộp**: `SELECT ma_vt, ma_kho, sum(sl_nhap) - sum(sl_xuat) AS ton FROM ct70 GROUP BY ma_vt, ma_kho`
- **Ghi chú nghiệp vụ**: Tồn kho chi tiết theo từng kho.
- **Số lượng cột trên giao diện**: 5 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 2 | Tên vật tư | `field_root (Tên vật tư)` | Trực tiếp hoặc format UI |
| 3 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 4 | Nhóm VT 6 (KH/NCC) | `ma_kh / ten_kh` | JOIN dmkh |
| 5 | Tên nhóm | `field_root (Tên nhóm)` | Trực tiếp hoặc format UI |

---

### 28. Tổng hợp nhập xuất tồn
- **Phân hệ**: `Kho vận`
- **Bảng vật lý trong DB**: `ct70, cdvt, dmvt`
- **Khóa liên kết / Logic gộp**: `Tồn đầu (cdvt) + Nhập (ct70) - Xuất (ct70) = Tồn cuối`
- **Ghi chú nghiệp vụ**: Báo cáo NXT kinh điển theo kỳ thời gian.
- **Số lượng cột trên giao diện**: 17 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 3 | Tên vật tư | `field_root (Tên vật tư)` | Trực tiếp hoặc format UI |
| 4 | Tên vật tư 2 | `field_root (Tên vật tư 2)` | Trực tiếp hoặc format UI |
| 5 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 6 | Tồn đầu | `field_root (Tồn đầu)` | Trực tiếp hoặc format UI |
| 7 | SL nhập | `so_luong / quantity` | SUM() nếu gộp dòng |
| 8 | SL xuất | `so_luong / quantity` | SUM() nếu gộp dòng |
| 9 | SL nhập kiểm kê | `so_luong / quantity` | SUM() nếu gộp dòng |
| 10 | SL xuất kiểm kê | `so_luong / quantity` | SUM() nếu gộp dòng |
| 11 | Chênh lệch kiểm kê trong kỳ | `field_root (Chênh lệch kiểm kê trong kỳ)` | Trực tiếp hoặc format UI |
| 12 | Tồn cuối | `field_root (Tồn cuối)` | Trực tiếp hoặc format UI |
| 13 | Nhóm VT 1 | `field_root (Nhóm VT 1)` | Trực tiếp hoặc format UI |
| 14 | Nhóm VT 2 | `field_root (Nhóm VT 2)` | Trực tiếp hoặc format UI |
| 15 | Nhóm VT 3 | `field_root (Nhóm VT 3)` | Trực tiếp hoặc format UI |
| 16 | Nhóm VT 4 | `field_root (Nhóm VT 4)` | Trực tiếp hoặc format UI |
| 17 | Nhóm VT 5 | `field_root (Nhóm VT 5)` | Trực tiếp hoặc format UI |

---

### 29. Tổng hợp nhập xuất tồn theo lô
- **Phân hệ**: `Kho vận`
- **Bảng vật lý trong DB**: `ct70, cdvt13, dmvt`
- **Khóa liên kết / Logic gộp**: `Tồn đầu lô (cdvt13) + Nhập (ct70) - Xuất (ct70) theo ma_lo`
- **Ghi chú nghiệp vụ**: Báo cáo NXT chi tiết theo từng lô hàng.
- **Số lượng cột trên giao diện**: 10 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 3 | Tên vật tư | `field_root (Tên vật tư)` | Trực tiếp hoặc format UI |
| 4 | Mã chuẩn | `field_root (Mã chuẩn)` | Trực tiếp hoặc format UI |
| 5 | Mã lô | `field_root (Mã lô)` | Trực tiếp hoặc format UI |
| 6 | Tồn đầu | `field_root (Tồn đầu)` | Trực tiếp hoặc format UI |
| 7 | Số lượng nhập | `so_luong / quantity` | SUM() nếu gộp dòng |
| 8 | Số lượng xuất | `so_luong / quantity` | SUM() nếu gộp dòng |
| 9 | Tồn cuối | `field_root (Tồn cuối)` | Trực tiếp hoặc format UI |
| 10 | Trạng thái lô | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |

---

### 30. Báo cáo tồn lô theo vị trí tất cả kho
- **Phân hệ**: `Kho vận`
- **Bảng vật lý trong DB**: `ct70, dmvitrikho, dmkho`
- **Khóa liên kết / Logic gộp**: `ct70 theo ma_vi_tri, ma_lo, ma_kho`
- **Ghi chú nghiệp vụ**: Báo cáo vị trí kho (Slot/Bin location).
- **Số lượng cột trên giao diện**: 10 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 3 | Tên vật tư | `field_root (Tên vật tư)` | Trực tiếp hoặc format UI |
| 4 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 5 | Nhóm VT 6 (NCC/KH) | `ma_kh / ten_kh` | JOIN dmkh |
| 6 | Mã lô | `field_root (Mã lô)` | Trực tiếp hoặc format UI |
| 7 | Trạng thái lô | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 8 | Mã kho | `ma_kh / ten_kh` | JOIN dmkh |
| 9 | Mã vị trí | `field_root (Mã vị trí)` | Trực tiếp hoặc format UI |
| 10 | Tồn vị trí | `field_root (Tồn vị trí)` | Trực tiếp hoặc format UI |

---

### 31. Báo cáo cấu trúc sản phẩm
- **Phân hệ**: `Sản xuất`
- **Bảng vật lý trong DB**: `mfbom, mfbom_material, dmvt`
- **Khóa liên kết / Logic gộp**: `mfbom.bom_code = mfbom_material.bom_code`
- **Ghi chú nghiệp vụ**: Cấu trúc BOM đa cấp, định mức NVL/linh kiện.
- **Số lượng cột trên giao diện**: 26 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Mã SP mẹ | `field_root (Mã SP mẹ)` | Trực tiếp hoặc format UI |
| 3 | Tên SP mẹ | `field_root (Tên SP mẹ)` | Trực tiếp hoặc format UI |
| 4 | Model SP mẹ | `field_root (Model SP mẹ)` | Trực tiếp hoặc format UI |
| 5 | Version | `field_root (Version)` | Trực tiếp hoặc format UI |
| 6 | Mã SP con | `field_root (Mã SP con)` | Trực tiếp hoặc format UI |
| 7 | Tên SP con | `field_root (Tên SP con)` | Trực tiếp hoặc format UI |
| 8 | ĐVT SP | `field_root (ĐVT SP)` | Trực tiếp hoặc format UI |
| 9 | SL SP | `so_luong / quantity` | SUM() nếu gộp dòng |
| 10 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 11 | Mã BTP/Vật tư | `field_root (Mã BTP/Vật tư)` | Trực tiếp hoặc format UI |
| 12 | Tên BTP/Vật tư | `field_root (Tên BTP/Vật tư)` | Trực tiếp hoặc format UI |
| 13 | Mã công đoạn | `field_root (Mã công đoạn)` | Trực tiếp hoặc format UI |
| 14 | Model BTP | `field_root (Model BTP)` | Trực tiếp hoặc format UI |
| 15 | Cấp BOM | `field_root (Cấp BOM)` | Trực tiếp hoặc format UI |
| 16 | SL định mức | `so_luong / quantity` | SUM() nếu gộp dòng |
| 17 | SL sản phẩm nvl | `so_luong / quantity` | SUM() nếu gộp dòng |
| 18 | Ngày ban hành | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 19 | Ngày kết thúc | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 20 | SL gate và runner | `so_luong / quantity` | SUM() nếu gộp dòng |
| 21 | Mã vật tư thay thế | `field_root (Mã vật tư thay thế)` | Trực tiếp hoặc format UI |
| 22 | Mã vật tư phụ | `field_root (Mã vật tư phụ)` | Trực tiếp hoặc format UI |
| 23 | Ngày ban hành | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 24 | Ngày ban hành | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 25 | Ngày kết thúc | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 26 | Ngày kết thúc | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |

---

### 32. Danh mục cấu trúc sản phẩm
- **Phân hệ**: `Sản xuất`
- **Bảng vật lý trong DB**: `mfbom, dmvt`
- **Khóa liên kết / Logic gộp**: `mfbom.product_code = dmvt.ma_vt`
- **Ghi chú nghiệp vụ**: Danh mục các phiên bản BOM theo sản phẩm.
- **Số lượng cột trên giao diện**: 5 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 3 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 4 | Tên sản phẩm | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 5 | Version | `field_root (Version)` | Trực tiếp hoặc format UI |

---

### 33. Khai báo quy trình sản xuất sản phẩm
- **Phân hệ**: `Sản xuất`
- **Bảng vật lý trong DB**: `mfrouting, mfdmcongdoan`
- **Khóa liên kết / Logic gộp**: `mfrouting.operation_code = mfdmcongdoan.operation_code`
- **Ghi chú nghiệp vụ**: Quy trình công nghệ (Routing), công đoạn sản xuất.
- **Số lượng cột trên giao diện**: 8 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 3 | Mã cấu trúc | `field_root (Mã cấu trúc)` | Trực tiếp hoặc format UI |
| 4 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 5 | Tên sản phẩm | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 6 | Version | `field_root (Version)` | Trực tiếp hoặc format UI |
| 7 | Mã quy trình | `field_root (Mã quy trình)` | Trực tiếp hoặc format UI |
| 8 | Mã ĐVCS | `field_root (Mã ĐVCS)` | Trực tiếp hoặc format UI |

---

### 34. Báo cáo lịch sử thay đổi bom list
- **Phân hệ**: `Sản xuất`
- **Bảng vật lý trong DB**: `mfbom_history, mfbom`
- **Khóa liên kết / Logic gộp**: `Lịch sử cập nhật BOM/ECN.`
- **Ghi chú nghiệp vụ**: Theo dõi các lần sửa đổi định mức BOM.
- **Số lượng cột trên giao diện**: 9 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Mã cấu trúc | `field_root (Mã cấu trúc)` | Trực tiếp hoặc format UI |
| 3 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 4 | Version | `field_root (Version)` | Trực tiếp hoặc format UI |
| 5 | Loại chỉnh sửa | `field_root (Loại chỉnh sửa)` | Trực tiếp hoặc format UI |
| 6 | Ngày chỉnh sửa | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 7 | Thời gian chỉnh sửa | `create_date || ' ' || create_time` | Ghép Ngày + Giờ |
| 8 | Người chỉnh sửa | `field_root (Người chỉnh sửa)` | Trực tiếp hoặc format UI |
| 9 | Nội dung chỉnh sửa | `field_root (Nội dung chỉnh sửa)` | Trực tiếp hoặc format UI |

---

### 35. Danh mục dây chuyền sản xuất
- **Phân hệ**: `Kỹ thuật`
- **Bảng vật lý trong DB**: `mfline, sys_station`
- **Khóa liên kết / Logic gộp**: `Danh mục line / chuyền sản xuất.`
- **Ghi chú nghiệp vụ**: Khai báo line xưởng ép nhựa / lắp ráp.
- **Số lượng cột trên giao diện**: 11 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 3 | Tên dây chuyền | `field_root (Tên dây chuyền)` | Trực tiếp hoặc format UI |
| 4 | Tên dây chuyền 2 | `field_root (Tên dây chuyền 2)` | Trực tiếp hoặc format UI |
| 5 | Mã nhóm dây chuyền 1 | `field_root (Mã nhóm dây chuyền 1)` | Trực tiếp hoặc format UI |
| 6 | Mã nhóm dây chuyền 2 | `field_root (Mã nhóm dây chuyền 2)` | Trực tiếp hoặc format UI |
| 7 | Mã nhóm dây chuyền 3 | `field_root (Mã nhóm dây chuyền 3)` | Trực tiếp hoặc format UI |
| 8 | Mã nhóm dây chuyền 3 | `field_root (Mã nhóm dây chuyền 3)` | Trực tiếp hoặc format UI |
| 9 | TK đăng nhập | `field_root (TK đăng nhập)` | Trực tiếp hoặc format UI |
| 10 | Mã ĐVCS | `field_root (Mã ĐVCS)` | Trực tiếp hoặc format UI |
| 11 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |

---

### 36. Danh mục khuôn
- **Phân hệ**: `Kỹ thuật`
- **Bảng vật lý trong DB**: `dmkhuon, dmhosokhuon`
- **Khóa liên kết / Logic gộp**: `dmkhuon.ma_khuon = dmhosokhuon.ma_khuon`
- **Ghi chú nghiệp vụ**: Danh mục khuôn đúc nhựa.
- **Số lượng cột trên giao diện**: 6 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Mã khuôn | `ma_kh / ten_kh` | JOIN dmkh |
| 3 | Tên khuôn | `ma_kh / ten_kh` | JOIN dmkh |
| 4 | Cavity | `field_root (Cavity)` | Trực tiếp hoặc format UI |
| 5 | TG thay khuôn TB (phút) | `ma_kh / ten_kh` | JOIN dmkh |
| 6 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |

---

### 37. Danh mục nguyên nhân dừng máy
- **Phân hệ**: `Kỹ thuật`
- **Bảng vật lý trong DB**: `_ma_nguyen_nhan, sys_dmdungmay`
- **Khóa liên kết / Logic gộp**: `Mã nguyên nhân dừng máy / downtime reasons.`
- **Ghi chú nghiệp vụ**: Lý do dừng máy: bảo dưỡng, hỏng khuôn, chờ NVL.
- **Số lượng cột trên giao diện**: 4 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Mã lỗi | `field_root (Mã lỗi)` | Trực tiếp hoặc format UI |
| 3 | Tên lỗi | `field_root (Tên lỗi)` | Trực tiếp hoặc format UI |
| 4 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |

---

### 38. Danh mục máy
- **Phân hệ**: `Kỹ thuật`
- **Bảng vật lý trong DB**: `dmmay, mfmachine`
- **Khóa liên kết / Logic gộp**: `Danh mục máy ép nhựa, máy phụ trợ.`
- **Ghi chú nghiệp vụ**: Thông số máy, lực kẹp, công suất.
- **Số lượng cột trên giao diện**: 10 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Mã máy | `field_root (Mã máy)` | Trực tiếp hoặc format UI |
| 3 | Tên máy | `field_root (Tên máy)` | Trực tiếp hoặc format UI |
| 4 | Mã ĐVCS | `field_root (Mã ĐVCS)` | Trực tiếp hoặc format UI |
| 5 | Thông số kỹ thuật | `field_root (Thông số kỹ thuật)` | Trực tiếp hoặc format UI |
| 6 | Công suất | `field_root (Công suất)` | Trực tiếp hoặc format UI |
| 7 | Hiệu suất | `field_root (Hiệu suất)` | Trực tiếp hoặc format UI |
| 8 | Máy đúc | `field_root (Máy đúc)` | Trực tiếp hoặc format UI |
| 9 | Số người vận hành | `field_root (Số người vận hành)` | Trực tiếp hoặc format UI |
| 10 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |

---

### 39. Hồ sơ khuôn
- **Phân hệ**: `Kỹ thuật`
- **Bảng vật lý trong DB**: `dmhosokhuon, dmhosokhuonsp`
- **Khóa liên kết / Logic gộp**: `dmhosokhuon.ma_khuon = dmhosokhuonsp.ma_khuon`
- **Ghi chú nghiệp vụ**: Theo dõi tổng số shot, số shot bảo hành, chu kỳ bảo dưỡng khuôn.
- **Số lượng cột trên giao diện**: 13 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Mã khuôn | `ma_kh / ten_kh` | JOIN dmkh |
| 3 | Tên khuôn | `ma_kh / ten_kh` | JOIN dmkh |
| 4 | Chiều dài dây thoát SP | `field_root (Chiều dài dây thoát SP)` | Trực tiếp hoặc format UI |
| 5 | Ngày bắt đầu làm khuôn | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 6 | Ngày bảo hành gần nhất | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 7 | Số shot bảo hành khuôn | `ma_kh / ten_kh` | JOIN dmkh |
| 8 | Đơn vị giá khác phun | `ma_kh / ten_kh` | JOIN dmkh |
| 9 | Đường kính vòng định vị | `field_root (Đường kính vòng định vị)` | Trực tiếp hoặc format UI |
| 10 | Trọng lượng khuôn (kg) | `ma_kh / ten_kh` | JOIN dmkh |
| 11 | Áp lực nén lớn nhất (MPA) | `field_root (Áp lực nén lớn nhất (MPA))` | Trực tiếp hoặc format UI |
| 12 | Áp lực phun lớn nhất | `field_root (Áp lực phun lớn nhất)` | Trực tiếp hoặc format UI |
| 13 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |

---

### 40. Báo cáo thông tin sản phẩm theo hồ sơ khuôn
- **Phân hệ**: `Kỹ thuật`
- **Bảng vật lý trong DB**: `dmhosokhuonsp, dmvt`
- **Khóa liên kết / Logic gộp**: `dmhosokhuonsp.ma_sp = dmvt.ma_vt`
- **Ghi chú nghiệp vụ**: Liên kết khuôn - sản phẩm, cavity khuôn.
- **Số lượng cột trên giao diện**: 10 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 3 | Tên sản phẩm | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 4 | Chính/Phụ | `field_root (Chính/Phụ)` | Trực tiếp hoặc format UI |
| 5 | Cavity sản phẩm | `field_root (Cavity sản phẩm)` | Trực tiếp hoặc format UI |
| 6 | Mã khuôn | `ma_kh / ten_kh` | JOIN dmkh |
| 7 | Tên khuôn | `ma_kh / ten_kh` | JOIN dmkh |
| 8 | ID cặp | `field_root (ID cặp)` | Trực tiếp hoặc format UI |
| 9 | Chu kỳ | `field_root (Chu kỳ)` | Trực tiếp hoặc format UI |
| 10 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |

---

### 41. Bảng kê lên khuôn
- **Phân hệ**: `Kỹ thuật`
- **Bảng vật lý trong DB**: `mes_oi_len_khuon, dmhosokhuon`
- **Khóa liên kết / Logic gộp**: `Nhật ký gá lắp khuôn lên máy ép.`
- **Ghi chú nghiệp vụ**: Lịch sử hạ/lên khuôn.
- **Số lượng cột trên giao diện**: 29 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 3 | Số WO | `mes_scheduling_code / so_ct` | Trực tiếp |
| 4 | Ngày kế hoạch | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 5 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 6 | Tên sản phẩm | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 7 | Mã khuôn lên | `ma_kh / ten_kh` | JOIN dmkh |
| 8 | Mã khuôn xuống | `ma_kh / ten_kh` | JOIN dmkh |
| 9 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 10 | Ngày BD lên khuôn | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 11 | TG BD lên khuôn | `ma_kh / ten_kh` | JOIN dmkh |
| 12 | NV thực hiện | `field_root (NV thực hiện)` | Trực tiếp hoặc format UI |
| 13 | Tên NV thực hiện | `field_root (Tên NV thực hiện)` | Trực tiếp hoặc format UI |
| 14 | TG lên khuôn | `ma_kh / ten_kh` | JOIN dmkh |
| 15 | Ngày KT lên khuôn | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 16 | TG KT lên khuôn | `ma_kh / ten_kh` | JOIN dmkh |
| 17 | Tổng TG phát sinh | `field_root (Tổng TG phát sinh)` | Trực tiếp hoặc format UI |
| 18 | Mã lỗi | `field_root (Mã lỗi)` | Trực tiếp hoặc format UI |
| 19 | Tên lỗi | `field_root (Tên lỗi)` | Trực tiếp hoặc format UI |
| 20 | Ngày BD ghi lỗi | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 21 | TG BD ghi lỗi | `field_root (TG BD ghi lỗi)` | Trực tiếp hoặc format UI |
| 22 | Ngày KT ghi lỗi | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 23 | TG KT ghi lỗi | `field_root (TG KT ghi lỗi)` | Trực tiếp hoặc format UI |
| 24 | TG xử lý | `field_root (TG xử lý)` | Trực tiếp hoặc format UI |
| 25 | NV xử lý | `field_root (NV xử lý)` | Trực tiếp hoặc format UI |
| 26 | Tên NV xử lý | `field_root (Tên NV xử lý)` | Trực tiếp hoặc format UI |
| 27 | Phương án xử lý | `field_root (Phương án xử lý)` | Trực tiếp hoặc format UI |
| 28 | Ghi chú | `field_root (Ghi chú)` | Trực tiếp hoặc format UI |
| 29 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |

---

### 42. Bảng kê setup, vận hành máy
- **Phân hệ**: `Kỹ thuật`
- **Bảng vật lý trong DB**: `mes_oi_setup_may`
- **Khóa liên kết / Logic gộp**: `Nhật ký setup thông số nhiệt độ, áp suất máy.`
- **Ghi chú nghiệp vụ**: Vận hành thông số máy ép.
- **Số lượng cột trên giao diện**: 26 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 3 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 4 | Tên sản phẩm | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 5 | Phiên bản | `field_root (Phiên bản)` | Trực tiếp hoặc format UI |
| 6 | Chu kỳ thực tế | `field_root (Chu kỳ thực tế)` | Trực tiếp hoặc format UI |
| 7 | Số PCS bỏ setup | `field_root (Số PCS bỏ setup)` | Trực tiếp hoặc format UI |
| 8 | Mã NV thực hiện | `field_root (Mã NV thực hiện)` | Trực tiếp hoặc format UI |
| 9 | Tên NV thực hiện | `field_root (Tên NV thực hiện)` | Trực tiếp hoặc format UI |
| 10 | Ngày BD setup | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 11 | TG BD setup | `field_root (TG BD setup)` | Trực tiếp hoặc format UI |
| 12 | Ngày KT setup | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 13 | TG KT setup | `field_root (TG KT setup)` | Trực tiếp hoặc format UI |
| 14 | Tổng TG setup | `field_root (Tổng TG setup)` | Trực tiếp hoặc format UI |
| 15 | Tổng TG phát sinh | `field_root (Tổng TG phát sinh)` | Trực tiếp hoặc format UI |
| 16 | Mã lỗi | `field_root (Mã lỗi)` | Trực tiếp hoặc format UI |
| 17 | Tên lỗi | `field_root (Tên lỗi)` | Trực tiếp hoặc format UI |
| 18 | Ngày BD ghi lỗi | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 19 | TG BD ghi lỗi | `field_root (TG BD ghi lỗi)` | Trực tiếp hoặc format UI |
| 20 | Ngày KT ghi lỗi | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 21 | TG KT ghi lỗi | `field_root (TG KT ghi lỗi)` | Trực tiếp hoặc format UI |
| 22 | TG xử lý | `field_root (TG xử lý)` | Trực tiếp hoặc format UI |
| 23 | Mã nhân viên xử lý | `field_root (Mã nhân viên xử lý)` | Trực tiếp hoặc format UI |
| 24 | Tên nhân viên xử lý | `field_root (Tên nhân viên xử lý)` | Trực tiếp hoặc format UI |
| 25 | Phương án xử lý | `field_root (Phương án xử lý)` | Trực tiếp hoặc format UI |
| 26 | Ghi chú | `field_root (Ghi chú)` | Trực tiếp hoặc format UI |

---

### 43. Bảng kê phát sinh trong sản xuất
- **Phân hệ**: `Kỹ thuật`
- **Bảng vật lý trong DB**: `mes_oi_phat_sinh`
- **Khóa liên kết / Logic gộp**: `Sự cố, phát sinh bất thường trong ca.`
- **Ghi chú nghiệp vụ**: Nhật ký phát sinh xưởng.
- **Số lượng cột trên giao diện**: 23 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 3 | Số WO | `mes_scheduling_code / so_ct` | Trực tiếp |
| 4 | Ngày kế hoạch | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 5 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 6 | Tên sản phẩm | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 7 | Mã khuôn | `ma_kh / ten_kh` | JOIN dmkh |
| 8 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 9 | Ngày BD sản xuất | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 10 | TG BD sản xuất | `field_root (TG BD sản xuất)` | Trực tiếp hoặc format UI |
| 11 | TG sản xuất | `field_root (TG sản xuất)` | Trực tiếp hoặc format UI |
| 12 | Ngày KT sản xuất | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 13 | Tổng TG phát sinh | `field_root (Tổng TG phát sinh)` | Trực tiếp hoặc format UI |
| 14 | Mã SP phụ nhận | `field_root (Mã SP phụ nhận)` | Trực tiếp hoặc format UI |
| 15 | Tên nguyên nhân | `field_root (Tên nguyên nhân)` | Trực tiếp hoặc format UI |
| 16 | Ngày BD ghi lỗi | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 17 | TG BD ghi lỗi | `field_root (TG BD ghi lỗi)` | Trực tiếp hoặc format UI |
| 18 | Ngày KT ghi lỗi | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 19 | TG KT ghi lỗi | `field_root (TG KT ghi lỗi)` | Trực tiếp hoặc format UI |
| 20 | TG xử lý | `field_root (TG xử lý)` | Trực tiếp hoặc format UI |
| 21 | Mã NV xử lý lỗi | `field_root (Mã NV xử lý lỗi)` | Trực tiếp hoặc format UI |
| 22 | Tên NV xử lý lỗi | `field_root (Tên NV xử lý lỗi)` | Trực tiếp hoặc format UI |
| 23 | TG KT ghi lỗi | `field_root (TG KT ghi lỗi)` | Trực tiếp hoặc format UI |

---

### 44. Lệnh sản xuất
- **Phân hệ**: `Sản xuất`
- **Bảng vật lý trong DB**: `mfwo, ph61, ct61`
- **Khóa liên kết / Logic gộp**: `Lệnh sản xuất (WO).`
- **Ghi chú nghiệp vụ**: Số lệnh, ngày bắt đầu, ngày kết thúc, SL kế hoạch.
- **Số lượng cột trên giao diện**: 16 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 3 | Ngày LSX | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 4 | Số LSX | `field_root (Số LSX)` | Trực tiếp hoặc format UI |
| 5 | Giao dịch | `field_root (Giao dịch)` | Trực tiếp hoặc format UI |
| 6 | Thủ khuôn Y/N | `ma_kh / ten_kh` | JOIN dmkh |
| 7 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 8 | Tên sản phẩm | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 9 | Version | `field_root (Version)` | Trực tiếp hoặc format UI |
| 10 | Mã phân xưởng | `field_root (Mã phân xưởng)` | Trực tiếp hoặc format UI |
| 11 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 12 | Tổng số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 13 | Số lượng HT | `so_luong / quantity` | SUM() nếu gộp dòng |
| 14 | Số lượng CL | `so_luong / quantity` | SUM() nếu gộp dòng |
| 15 | Số lượng OK | `so_luong / quantity` | SUM() nếu gộp dòng |
| 16 | Số lượng NG | `so_luong / quantity` | SUM() nếu gộp dòng |

---

### 45. Lịch sản xuất (Import)
- **Phân hệ**: `Sản xuất`
- **Bảng vật lý trong DB**: `mfkhsx, mfkhsx_po_fc`
- **Khóa liên kết / Logic gộp**: `Lịch sản xuất ngày/tuần.`
- **Ghi chú nghiệp vụ**: Kế hoạch lịch sản xuất chi tiết theo ca/máy.
- **Số lượng cột trên giao diện**: 9 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 3 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 4 | Ngày kế hoạch | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 5 | Mã tổ | `field_root (Mã tổ)` | Trực tiếp hoặc format UI |
| 6 | Tên tổ | `field_root (Tên tổ)` | Trực tiếp hoặc format UI |
| 7 | Mã phân xưởng | `field_root (Mã phân xưởng)` | Trực tiếp hoặc format UI |
| 8 | Tên phân xưởng | `field_root (Tên phân xưởng)` | Trực tiếp hoặc format UI |
| 9 | Mã ĐVCS | `field_root (Mã ĐVCS)` | Trực tiếp hoặc format UI |

---

### 46. Bảng kê phân bổ thời gian dừng chuyền giữa các phiên làm việc
- **Phân hệ**: `Sản xuất`
- **Bảng vật lý trong DB**: `mes_oi_downtime, _ma_nguyen_nhan`
- **Khóa liên kết / Logic gộp**: `Thời gian dừng máy theo ca/phiên.`
- **Ghi chú nghiệp vụ**: Phân bổ downtime.
- **Số lượng cột trên giao diện**: 16 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 3 | Mã công đoạn | `field_root (Mã công đoạn)` | Trực tiếp hoặc format UI |
| 4 | Phiên làm việc 1 | `field_root (Phiên làm việc 1)` | Trực tiếp hoặc format UI |
| 5 | Phiên làm việc 2 | `field_root (Phiên làm việc 2)` | Trực tiếp hoặc format UI |
| 6 | Ngày bắt đầu | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 7 | Giờ bắt đầu | `time0 / create_time` | Định dạng HH:mm:ss |
| 8 | Tên nguyên nhân | `field_root (Tên nguyên nhân)` | Trực tiếp hoặc format UI |
| 9 | Mã nguyên nhân | `field_root (Mã nguyên nhân)` | Trực tiếp hoặc format UI |
| 10 | Ngày kết thúc | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 11 | Giờ kết thúc | `time0 / create_time` | Định dạng HH:mm:ss |
| 12 | Thời gian dừng (phút) | `create_date || ' ' || create_time` | Ghép Ngày + Giờ |
| 13 | Ngày kết thúc | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 14 | Giờ kết thúc | `time0 / create_time` | Định dạng HH:mm:ss |
| 15 | Thời gian dừng giữa 2 phiên (phút) | `create_date || ' ' || create_time` | Ghép Ngày + Giờ |
| 16 | Giờ bắt đầu | `time0 / create_time` | Định dạng HH:mm:ss |

---

### 47. Bảng thống kê đăng ký NG trong sản xuất
- **Phân hệ**: `Sản xuất`
- **Bảng vật lý trong DB**: `mes_oi_ng, sys_listoptions`
- **Khóa liên kết / Logic gộp**: `Ghi nhận sản lượng phế phẩm / NG.`
- **Ghi chú nghiệp vụ**: NG theo công đoạn, mã lỗi.
- **Số lượng cột trên giao diện**: 19 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 3 | Ngày kế hoạch | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 4 | Ngày sản xuất thực tế | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 5 | Số LSX | `field_root (Số LSX)` | Trực tiếp hoặc format UI |
| 6 | Số WO | `mes_scheduling_code / so_ct` | Trực tiếp |
| 7 | Phiên làm việc | `field_root (Phiên làm việc)` | Trực tiếp hoặc format UI |
| 8 | Ngày bắt đầu | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 9 | Giờ bắt đầu | `time0 / create_time` | Định dạng HH:mm:ss |
| 10 | Ngày kết thúc | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 11 | Giờ kết thúc | `time0 / create_time` | Định dạng HH:mm:ss |
| 12 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 13 | Tên sản phẩm | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 14 | SL kế hoạch | `so_luong / quantity` | SUM() nếu gộp dòng |
| 15 | SL sản xuất thực tế | `so_luong / quantity` | SUM() nếu gộp dòng |
| 16 | SL NG | `so_luong / quantity` | SUM() nếu gộp dòng |
| 17 | Nhóm vật tư 6 | `field_root (Nhóm vật tư 6)` | Trực tiếp hoặc format UI |
| 18 | Tên khách hàng | `ma_kh / ten_kh` | JOIN dmkh |
| 19 | Nhóm khách hàng 1 | `ma_kh / ten_kh` | JOIN dmkh |

---

### 48. Bảng kê NG linh kiện
- **Phân hệ**: `Sản xuất`
- **Bảng vật lý trong DB**: `mes_oi_ng_linh_kien`
- **Khóa liên kết / Logic gộp**: `NG linh kiện đầu vào / lắp ráp.`
- **Ghi chú nghiệp vụ**: Phế phẩm linh kiện.
- **Số lượng cột trên giao diện**: 18 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Work Order | `mes_scheduling_code / so_ct` | Trực tiếp |
| 3 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 4 | Phiên làm việc | `field_root (Phiên làm việc)` | Trực tiếp hoặc format UI |
| 5 | Ngày bắt đầu | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 6 | Giờ bắt đầu | `time0 / create_time` | Định dạng HH:mm:ss |
| 7 | Ngày kết thúc | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 8 | Giờ kết thúc | `time0 / create_time` | Định dạng HH:mm:ss |
| 9 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 10 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 11 | Tên vật tư | `field_root (Tên vật tư)` | Trực tiếp hoặc format UI |
| 12 | Mã lỗi | `field_root (Mã lỗi)` | Trực tiếp hoặc format UI |
| 13 | Tên lỗi | `field_root (Tên lỗi)` | Trực tiếp hoặc format UI |
| 14 | Mã lỗi | `field_root (Mã lỗi)` | Trực tiếp hoặc format UI |
| 15 | Nhóm thao tác | `field_root (Nhóm thao tác)` | Trực tiếp hoặc format UI |
| 16 | Phân loại | `field_root (Phân loại)` | Trực tiếp hoặc format UI |
| 17 | Ngày đăng ký | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 18 | Giờ đăng ký | `time0 / create_time` | Định dạng HH:mm:ss |

---

### 49. Bảng thống kê cấp nguyên vật liệu
- **Phân hệ**: `MES`
- **Bảng vật lý trong DB**: `mes_oi_dong_thung, intem_log, ct70`
- **Khóa liên kết / Logic gộp**: `Cấp NVL theo lệnh sản xuất / WO.`
- **Ghi chú nghiệp vụ**: SL yêu cầu, SL đã cấp, SL tồn NVL.
- **Số lượng cột trên giao diện**: 18 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Mã ĐVCS | `field_root (Mã ĐVCS)` | Trực tiếp hoặc format UI |
| 3 | Ngày thực hiện | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 4 | Phiên làm việc | `field_root (Phiên làm việc)` | Trực tiếp hoặc format UI |
| 5 | Số W/O | `field_root (Số W/O)` | Trực tiếp hoặc format UI |
| 6 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 7 | Tên sản phẩm | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 8 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 9 | Tên vật tư | `field_root (Tên vật tư)` | Trực tiếp hoặc format UI |
| 10 | Mã vật tư thay thế | `field_root (Mã vật tư thay thế)` | Trực tiếp hoặc format UI |
| 11 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 12 | SL yêu cầu | `so_luong / quantity` | SUM() nếu gộp dòng |
| 13 | SL đã cấp | `so_luong / quantity` | SUM() nếu gộp dòng |
| 14 | SL tồn (theo vật tư thay thế) | `so_luong / quantity` | SUM() nếu gộp dòng |
| 15 | Tổng SL đã cấp (theo vật tư thay thế) | `so_luong / quantity` | SUM() nếu gộp dòng |
| 16 | User cấp liệu | `field_root (User cấp liệu)` | Trực tiếp hoặc format UI |
| 17 | Số phiếu xuất kho | `ma_kh / ten_kh` | JOIN dmkh |
| 18 | SL tồn | `so_luong / quantity` | SUM() nếu gộp dòng |

---

### 50. Bảng kê đóng gói, đóng thùng
- **Phân hệ**: `MES`
- **Bảng vật lý trong DB**: `mes_oi_dong_thung, mes_oi_dong_thung1, intem_carton_log`
- **Khóa liên kết / Logic gộp**: `GROUP BY serial_tem_thung, station_code, product_code`
- **Ghi chú nghiệp vụ**: Đóng thùng thành phẩm: serial thùng, số lượng thùng, thời gian đóng.
- **Số lượng cột trên giao diện**: 15 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Ngày kế hoạch | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 3 | Ngày sản xuất thực tế | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 4 | Phiên làm việc | `field_root (Phiên làm việc)` | Trực tiếp hoặc format UI |
| 5 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 6 | Số WO | `mes_scheduling_code / so_ct` | Trực tiếp |
| 7 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 8 | Tên sản phẩm | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 9 | SL kế hoạch | `so_luong / quantity` | SUM() nếu gộp dòng |
| 10 | Số lượng thực tế | `so_luong / quantity` | SUM() nếu gộp dòng |
| 11 | Số lượng theo thùng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 12 | QM thùng TP | `serial_tem_thung / id_carton` | Khóa định danh thùng |
| 13 | Serial thùng TP | `serial_tem_thung / id_carton` | Khóa định danh thùng |
| 14 | Thời gian đóng thùng | `create_date || ' ' || create_time` | Ghép Ngày + Giờ |
| 15 | Phân loại | `field_root (Phân loại)` | Trực tiếp hoặc format UI |

---

### 51. Bảng kê gộp, tách thùng
- **Phân hệ**: `MES`
- **Bảng vật lý trong DB**: `intem_carton_log, intem_log`
- **Khóa liên kết / Logic gộp**: `intem_carton_log.id_carton (tem cũ) -> id_carton_new (tem mới)`
- **Ghi chú nghiệp vụ**: Lịch sử gộp hoặc chia nhỏ thùng hàng.
- **Số lượng cột trên giao diện**: 15 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Ngày ghi nhận | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 2 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 3 | Tên sản phẩm | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 4 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 5 | ID Tem cũ | `field_root (ID Tem cũ)` | Trực tiếp hoặc format UI |
| 6 | Mã thùng | `serial_tem_thung / id_carton` | Khóa định danh thùng |
| 7 | Tên thùng | `serial_tem_thung / id_carton` | Khóa định danh thùng |
| 8 | Số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 9 | ID Tem mới | `field_root (ID Tem mới)` | Trực tiếp hoặc format UI |
| 10 | Mã thùng | `serial_tem_thung / id_carton` | Khóa định danh thùng |
| 11 | Tên thùng | `serial_tem_thung / id_carton` | Khóa định danh thùng |
| 12 | Số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 13 | Tổng thùng tách | `serial_tem_thung / id_carton` | Khóa định danh thùng |
| 14 | Giờ tạo | `time0 / create_time` | Định dạng HH:mm:ss |
| 15 | User tạo | `field_root (User tạo)` | Trực tiếp hoặc format UI |

---

### 52. Bảng kê Work Order
- **Phân hệ**: `MES`
- **Bảng vật lý trong DB**: `mes_scheduling, mes_oi_rework, mfkhsx`
- **Khóa liên kết / Logic gộp**: `Số WO, mã sản phẩm, phiên làm việc, tiến độ.`
- **Ghi chú nghiệp vụ**: Theo dõi tiến độ WO xưởng.
- **Số lượng cột trên giao diện**: 19 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Mã WO | `mes_scheduling_code / so_ct` | Trực tiếp |
| 3 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 4 | Tên sản phẩm | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 5 | Version BOM | `field_root (Version BOM)` | Trực tiếp hoặc format UI |
| 6 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 7 | Mã khuôn | `ma_kh / ten_kh` | JOIN dmkh |
| 8 | ID cặp | `field_root (ID cặp)` | Trực tiếp hoặc format UI |
| 9 | Mã tổ | `field_root (Mã tổ)` | Trực tiếp hoặc format UI |
| 10 | Số lượng KH | `so_luong / quantity` | SUM() nếu gộp dòng |
| 11 | Số lượng thực hiện | `so_luong / quantity` | SUM() nếu gộp dòng |
| 12 | Số lượng đóng gói | `so_luong / quantity` | SUM() nếu gộp dòng |
| 13 | Ngày bắt đầu | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 14 | Ngày kết thúc | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 15 | Ngày kết thúc | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 16 | Ngày kết thúc | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 17 | Số lệnh sản xuất | `mes_scheduling_code / so_ct` | Trực tiếp |
| 18 | Số CT lịch sản xuất | `field_root (Số CT lịch sản xuất)` | Trực tiếp hoặc format UI |
| 19 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |

---

### 53. Bảng kê bổ sung shot
- **Phân hệ**: `MES`
- **Bảng vật lý trong DB**: `mes_oi_bo_shot, dmhosokhuon`
- **Khóa liên kết / Logic gộp**: `mes_oi_bo_shot.mes_scheduling_code, machine_code, station_code`
- **Ghi chú nghiệp vụ**: Ghi nhận shot đúc ép bổ sung.
- **Số lượng cột trên giao diện**: 12 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Work order | `mes_scheduling_code / so_ct` | Trực tiếp |
| 3 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 4 | Phiên làm việc | `field_root (Phiên làm việc)` | Trực tiếp hoặc format UI |
| 5 | Mã sản phẩm chính | `ma_vt / product_code` | Trực tiếp |
| 6 | Tên sản phẩm | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 7 | Ngày bổ sung shot | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 8 | Giờ bổ sung shot | `time0 / create_time` | Định dạng HH:mm:ss |
| 9 | Số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 10 | Mã NV bổ sung shot | `field_root (Mã NV bổ sung shot)` | Trực tiếp hoặc format UI |
| 11 | Tên nhân viên | `field_root (Tên nhân viên)` | Trực tiếp hoặc format UI |
| 12 | Ghi chú | `field_root (Ghi chú)` | Trực tiếp hoặc format UI |

---

### 54. Bảng kê chi tiết bỏ shot
- **Phân hệ**: `MES`
- **Bảng vật lý trong DB**: `mes_oi_bo_shot`
- **Khóa liên kết / Logic gộp**: `mes_oi_bo_shot WHERE start_yn = 0 OR quantity < 0`
- **Ghi chú nghiệp vụ**: Shot bị loại trừ khỏi sản lượng.
- **Số lượng cột trên giao diện**: 13 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Work Order | `mes_scheduling_code / so_ct` | Trực tiếp |
| 3 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 4 | Phiên làm việc | `field_root (Phiên làm việc)` | Trực tiếp hoặc format UI |
| 5 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 6 | Tên sản phẩm | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 7 | Số cavity | `field_root (Số cavity)` | Trực tiếp hoặc format UI |
| 8 | Ngày bỏ shot | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 9 | Giờ bỏ shot | `time0 / create_time` | Định dạng HH:mm:ss |
| 10 | Số shot bỏ | `field_root (Số shot bỏ)` | Trực tiếp hoặc format UI |
| 11 | SL hàng bỏ | `so_luong / quantity` | SUM() nếu gộp dòng |
| 12 | Lý do bỏ shot | `field_root (Lý do bỏ shot)` | Trực tiếp hoặc format UI |
| 13 | Tên nhân viên | `field_root (Tên nhân viên)` | Trực tiếp hoặc format UI |

---

### 55. Bảng kê thay đổi cavity
- **Phân hệ**: `MES`
- **Bảng vật lý trong DB**: `mes_oi_bo_shot, dmhosokhuonsp`
- **Khóa liên kết / Logic gộp**: `Thay đổi số cavity hoạt động của khuôn.`
- **Ghi chú nghiệp vụ**: Biến động số cavity đúc.
- **Số lượng cột trên giao diện**: 13 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Work Order | `mes_scheduling_code / so_ct` | Trực tiếp |
| 3 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 4 | Phiên làm việc | `field_root (Phiên làm việc)` | Trực tiếp hoặc format UI |
| 5 | Mã khuôn | `ma_kh / ten_kh` | JOIN dmkh |
| 6 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 7 | Tên sản phẩm | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 8 | Chính/Phụ | `field_root (Chính/Phụ)` | Trực tiếp hoặc format UI |
| 9 | ID cặp | `field_root (ID cặp)` | Trực tiếp hoặc format UI |
| 10 | Cavity gốc | `field_root (Cavity gốc)` | Trực tiếp hoặc format UI |
| 11 | Cavity sau thay đổi | `field_root (Cavity sau thay đổi)` | Trực tiếp hoặc format UI |
| 12 | Ngày thay đổi cavity | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 13 | Giờ thay đổi cavity | `time0 / create_time` | Định dạng HH:mm:ss |

---

### 56. Báo cáo thu hồi NVL
- **Phân hệ**: `MES`
- **Bảng vật lý trong DB**: `mes_oi_thu_hoi_nvl, ct70`
- **Khóa liên kết / Logic gộp**: `Thu hồi nhựa thừa, cuống phun sau ca.`
- **Ghi chú nghiệp vụ**: Vật tư thu hồi.
- **Số lượng cột trên giao diện**: 14 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Work Order gần nhất | `mes_scheduling_code / so_ct` | Trực tiếp |
| 3 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 4 | Mã máy | `field_root (Mã máy)` | Trực tiếp hoặc format UI |
| 5 | Phiên làm việc gần nhất | `field_root (Phiên làm việc gần nhất)` | Trực tiếp hoặc format UI |
| 6 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 7 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 8 | Mã vật tư thay thế | `field_root (Mã vật tư thay thế)` | Trực tiếp hoặc format UI |
| 9 | Ngày thu hồi | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 10 | Giờ thu hồi | `time0 / create_time` | Định dạng HH:mm:ss |
| 11 | Số lượng thu hồi thực tế | `so_luong / quantity` | SUM() nếu gộp dòng |
| 12 | Số lượng thu hồi thực tế (theo vật tư thay thế) | `so_luong / quantity` | SUM() nếu gộp dòng |
| 13 | Thu hồi (theo định mức) | `field_root (Thu hồi (theo định mức))` | Trực tiếp hoặc format UI |
| 14 | Chênh lệch | `field_root (Chênh lệch)` | Trực tiếp hoặc format UI |

---

### 57. Báo cáo kết quả vận hành theo phiên làm việc
- **Phân hệ**: `MES`
- **Bảng vật lý trong DB**: `mes_oi_dong_thung, mes_oi_bo_shot, mes_scheduling`
- **Khóa liên kết / Logic gộp**: `Tổng hợp sản lượng đạt/NG theo từng ca.`
- **Ghi chú nghiệp vụ**: Báo cáo ca sản xuất.
- **Số lượng cột trên giao diện**: 31 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Số LSX | `field_root (Số LSX)` | Trực tiếp hoặc format UI |
| 3 | Mã Work Order | `mes_scheduling_code / so_ct` | Trực tiếp |
| 4 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 5 | Mã công đoạn | `field_root (Mã công đoạn)` | Trực tiếp hoặc format UI |
| 6 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 7 | Tên sản phẩm | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 8 | Mã khuôn | `ma_kh / ten_kh` | JOIN dmkh |
| 9 | Phiên làm việc | `field_root (Phiên làm việc)` | Trực tiếp hoặc format UI |
| 10 | Ngày SX kế hoạch | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 11 | Ngày BD | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 12 | Giờ BD | `time0 / create_time` | Định dạng HH:mm:ss |
| 13 | Ngày KT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 14 | Giờ KT | `time0 / create_time` | Định dạng HH:mm:ss |
| 15 | Thời gian vận hành (Phút) | `create_date || ' ' || create_time` | Ghép Ngày + Giờ |
| 16 | Thời gian dừng máy (Phút) | `create_date || ' ' || create_time` | Ghép Ngày + Giờ |
| 17 | Thời gian SX thực tế (Phút) | `create_date || ' ' || create_time` | Ghép Ngày + Giờ |
| 18 | SL kế hoạch | `so_luong / quantity` | SUM() nếu gộp dòng |
| 19 | SL thực hiện | `so_luong / quantity` | SUM() nếu gộp dòng |
| 20 | SL thực tế OK | `so_luong / quantity` | SUM() nếu gộp dòng |
| 21 | SL thực tế NG | `so_luong / quantity` | SUM() nếu gộp dòng |
| 22 | Tổng NG linh kiện | `field_root (Tổng NG linh kiện)` | Trực tiếp hoặc format UI |
| 23 | SL đóng gói | `so_luong / quantity` | SUM() nếu gộp dòng |
| 24 | SL bỏ shot | `so_luong / quantity` | SUM() nếu gộp dòng |
| 25 | SL bổ sung shot | `so_luong / quantity` | SUM() nếu gộp dòng |
| 26 | SL chênh lệch | `so_luong / quantity` | SUM() nếu gộp dòng |
| 27 | % Hoàn thành | `field_root (% Hoàn thành)` | Trực tiếp hoặc format UI |
| 28 | Tỷ lệ NG | `field_root (Tỷ lệ NG)` | Trực tiếp hoặc format UI |
| 29 | Số phiếu nhập kho | `ma_kh / ten_kh` | JOIN dmkh |
| 30 | Chu kỳ kế hoạch (s) | `field_root (Chu kỳ kế hoạch (s))` | Trực tiếp hoặc format UI |
| 31 | Chu kỳ set up máy (s) | `field_root (Chu kỳ set up máy (s))` | Trực tiếp hoặc format UI |

---

### 58. Báo cáo Tổng hợp hàng NG theo phiên làm việc
- **Phân hệ**: `MES`
- **Bảng vật lý trong DB**: `mes_oi_ng, mes_scheduling`
- **Khóa liên kết / Logic gộp**: `GROUP BY station_code, date0, ma_loi`
- **Ghi chú nghiệp vụ**: Tỷ lệ NG theo phiên.
- **Số lượng cột trên giao diện**: 19 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 3 | Ngày kế hoạch | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 4 | Ngày sản xuất thực tế | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 5 | Số LSX | `field_root (Số LSX)` | Trực tiếp hoặc format UI |
| 6 | Số WO | `mes_scheduling_code / so_ct` | Trực tiếp |
| 7 | Phiên làm việc | `field_root (Phiên làm việc)` | Trực tiếp hoặc format UI |
| 8 | Ngày bắt đầu | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 9 | Giờ bắt đầu | `time0 / create_time` | Định dạng HH:mm:ss |
| 10 | Ngày kết thúc | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 11 | Giờ kết thúc | `time0 / create_time` | Định dạng HH:mm:ss |
| 12 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 13 | Tên sản phẩm | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 14 | SL kế hoạch | `so_luong / quantity` | SUM() nếu gộp dòng |
| 15 | SL sản xuất thực tế | `so_luong / quantity` | SUM() nếu gộp dòng |
| 16 | SL NG | `so_luong / quantity` | SUM() nếu gộp dòng |
| 17 | Nhóm vật tư 6 | `field_root (Nhóm vật tư 6)` | Trực tiếp hoặc format UI |
| 18 | Tên khách hàng | `ma_kh / ten_kh` | JOIN dmkh |
| 19 | Nhóm khách hàng 1 | `ma_kh / ten_kh` | JOIN dmkh |

---

### 59. Báo cáo thời gian dừng chuyền theo từng phiên làm việc
- **Phân hệ**: `MES`
- **Bảng vật lý trong DB**: `mes_oi_downtime`
- **Khóa liên kết / Logic gộp**: `Downtime theo ca.`
- **Ghi chú nghiệp vụ**: Thời gian dừng máy trong ca.
- **Số lượng cột trên giao diện**: 22 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Mã Work Order | `mes_scheduling_code / so_ct` | Trực tiếp |
| 3 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 4 | Mã công đoạn | `field_root (Mã công đoạn)` | Trực tiếp hoặc format UI |
| 5 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 6 | Phiên làm việc | `field_root (Phiên làm việc)` | Trực tiếp hoặc format UI |
| 7 | Ngày BD | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 8 | Giờ BD | `time0 / create_time` | Định dạng HH:mm:ss |
| 9 | Ngày KT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 10 | Giờ KT | `time0 / create_time` | Định dạng HH:mm:ss |
| 11 | Mã nguyên nhân | `field_root (Mã nguyên nhân)` | Trực tiếp hoặc format UI |
| 12 | Thời gian dừng từ | `create_date || ' ' || create_time` | Ghép Ngày + Giờ |
| 13 | Thời gian dừng đến | `create_date || ' ' || create_time` | Ghép Ngày + Giờ |
| 14 | Thời gian dừng (Phút) | `create_date || ' ' || create_time` | Ghép Ngày + Giờ |
| 15 | Mã NV xử lý | `field_root (Mã NV xử lý)` | Trực tiếp hoặc format UI |
| 16 | Tên NV xử lý | `field_root (Tên NV xử lý)` | Trực tiếp hoặc format UI |
| 17 | Phương án xử lý | `field_root (Phương án xử lý)` | Trực tiếp hoặc format UI |
| 18 | Ghi chú | `field_root (Ghi chú)` | Trực tiếp hoặc format UI |
| 19 | Nhóm lỗi 1 | `field_root (Nhóm lỗi 1)` | Trực tiếp hoặc format UI |
| 20 | Nhóm lỗi 2 | `field_root (Nhóm lỗi 2)` | Trực tiếp hoặc format UI |
| 21 | Nhóm lỗi 3 | `field_root (Nhóm lỗi 3)` | Trực tiếp hoặc format UI |
| 22 | Mã NV nhận | `field_root (Mã NV nhận)` | Trực tiếp hoặc format UI |

---

### 60. Báo cáo version OI theo mã dây chuyền
- **Phân hệ**: `MES`
- **Bảng vật lý trong DB**: `sys_oi_version`
- **Khóa liên kết / Logic gộp**: `Phiên bản phần mềm OI trên các line.`
- **Ghi chú nghiệp vụ**: Quản lý phiên bản máy trạm OI xưởng.
- **Số lượng cột trên giao diện**: 5 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 3 | Version | `field_root (Version)` | Trực tiếp hoặc format UI |
| 4 | Check version | `field_root (Check version)` | Trực tiếp hoặc format UI |
| 5 | IP | `field_root (IP)` | Trực tiếp hoặc format UI |

---

### 61. Báo cáo NVL sử dụng theo từng phiên làm việc (theo mã lô KH)
- **Phân hệ**: `MES`
- **Bảng vật lý trong DB**: `mes_oi_cap_lieu, intem_log`
- **Khóa liên kết / Logic gộp**: `Truy xuất nguồn gốc lô hạt nhựa / NVL theo ca.`
- **Ghi chú nghiệp vụ**: Lot traceability NVL.
- **Số lượng cột trên giao diện**: 22 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Mã Work Order | `mes_scheduling_code / so_ct` | Trực tiếp |
| 3 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 4 | Mã công đoạn | `field_root (Mã công đoạn)` | Trực tiếp hoặc format UI |
| 5 | Mã dây chuyền | `field_root (Mã dây chuyền)` | Trực tiếp hoặc format UI |
| 6 | Phiên làm việc | `field_root (Phiên làm việc)` | Trực tiếp hoặc format UI |
| 7 | Ngày BD | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 8 | Giờ BD | `time0 / create_time` | Định dạng HH:mm:ss |
| 9 | Ngày KT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 10 | Giờ KT | `time0 / create_time` | Định dạng HH:mm:ss |
| 11 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 12 | Tên vật tư | `field_root (Tên vật tư)` | Trực tiếp hoặc format UI |
| 13 | Mã vật tư thay thế | `field_root (Mã vật tư thay thế)` | Trực tiếp hoặc format UI |
| 14 | Số lượng cấp | `so_luong / quantity` | SUM() nếu gộp dòng |
| 15 | Số lượng theo vật tư thay thế | `so_luong / quantity` | SUM() nếu gộp dòng |
| 16 | SL sử dụng theo định mức | `so_luong / quantity` | SUM() nếu gộp dòng |
| 17 | SL còn lại | `so_luong / quantity` | SUM() nếu gộp dòng |
| 18 | Số lượng tồn gửi lại | `so_luong / quantity` | SUM() nếu gộp dòng |
| 19 | Số lượng | `so_luong / quantity` | SUM() nếu gộp dòng |
| 20 | Mã lô | `field_root (Mã lô)` | Trực tiếp hoặc format UI |
| 21 | Seri | `field_root (Seri)` | Trực tiếp hoặc format UI |
| 22 | Mã lô NCC | `field_root (Mã lô NCC)` | Trực tiếp hoặc format UI |

---

### 62. Danh mục bài kiểm tra
- **Phân hệ**: `QC`
- **Bảng vật lý trong DB**: `qc_dmbaikiemtra`
- **Khóa liên kết / Logic gộp**: `Danh mục các tiêu chí đo kiểm.`
- **Ghi chú nghiệp vụ**: Checksheet kiểm tra.
- **Số lượng cột trên giao diện**: 5 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Mã bài kiểm tra | `field_root (Mã bài kiểm tra)` | Trực tiếp hoặc format UI |
| 3 | Tên bài kiểm tra | `field_root (Tên bài kiểm tra)` | Trực tiếp hoặc format UI |
| 4 | Danh sách ĐVCS | `field_root (Danh sách ĐVCS)` | Trực tiếp hoặc format UI |
| 5 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |

---

### 63. Phiếu kiểm tra chất lượng IQC
- **Phân hệ**: `QC`
- **Bảng vật lý trong DB**: `qc_iqc, intem_log`
- **Khóa liên kết / Logic gộp**: `Kiểm tra chất lượng NVL đầu vào (IQC).`
- **Ghi chú nghiệp vụ**: Kết quả pass/reject lô nguyên vật liệu.
- **Số lượng cột trên giao diện**: 13 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 3 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 4 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 5 | Tên giao dịch | `field_root (Tên giao dịch)` | Trực tiếp hoặc format UI |
| 6 | Mã NCC | `field_root (Mã NCC)` | Trực tiếp hoặc format UI |
| 7 | Mã ĐVCS | `field_root (Mã ĐVCS)` | Trực tiếp hoặc format UI |
| 8 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 9 | Tên vật tư | `field_root (Tên vật tư)` | Trực tiếp hoặc format UI |
| 10 | Số lượng mẫu | `so_luong / quantity` | SUM() nếu gộp dòng |
| 11 | Số CT tham chiếu | `field_root (Số CT tham chiếu)` | Trực tiếp hoặc format UI |
| 12 | Kết quả | `field_root (Kết quả)` | Trực tiếp hoặc format UI |
| 13 | ID tem túi | `field_root (ID tem túi)` | Trực tiếp hoặc format UI |

---

### 64. Phiếu kiểm tra chất lượng IPQC
- **Phân hệ**: `QC`
- **Bảng vật lý trong DB**: `qc_ipqc, mes_oi_dong_thung`
- **Khóa liên kết / Logic gộp**: `Kiểm tra chất lượng trên chuyền (IPQC).`
- **Ghi chú nghiệp vụ**: Kiểm tra công đoạn sản xuất.
- **Số lượng cột trên giao diện**: 13 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | Lịch sử cập nhật | `field_root (Lịch sử cập nhật)` | Trực tiếp hoặc format UI |
| 2 | Trạng thái | `status / statusname` | Map qua sys_dmtt hoặc sys_listoptions |
| 3 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 4 | Số CT | `field_root (Số CT)` | Trực tiếp hoặc format UI |
| 5 | Tên giao dịch | `field_root (Tên giao dịch)` | Trực tiếp hoặc format UI |
| 6 | Mã ĐVCS | `field_root (Mã ĐVCS)` | Trực tiếp hoặc format UI |
| 7 | Mã sản phẩm | `ma_vt / product_code` | Trực tiếp |
| 8 | Tên sản phẩm | `ten_vt / product_name` | JOIN dmvt.ten_vt |
| 9 | Mã công đoạn | `field_root (Mã công đoạn)` | Trực tiếp hoặc format UI |
| 10 | Số lượng kiểm tra | `so_luong / quantity` | SUM() nếu gộp dòng |
| 11 | Số lệnh SX | `mes_scheduling_code / so_ct` | Trực tiếp |
| 12 | Kết quả | `field_root (Kết quả)` | Trực tiếp hoặc format UI |
| 13 | ID tem túi | `field_root (ID tem túi)` | Trực tiếp hoặc format UI |

---

### 65. Bảng kê phiếu IQC, IPQC
- **Phân hệ**: `QC`
- **Bảng vật lý trong DB**: `qc_iqc, qc_ipqc`
- **Khóa liên kết / Logic gộp**: `Bảng kê tổng hợp các phiếu kiểm tra QC.`
- **Ghi chú nghiệp vụ**: Sổ theo dõi QC.
- **Số lượng cột trên giao diện**: 24 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Loại phiếu | `field_root (Loại phiếu)` | Trực tiếp hoặc format UI |
| 3 | Ngày CT | `ngay_ct / date0 / create_date` | Định dạng YYYY-MM-DD |
| 4 | Nhà cung cấp | `field_root (Nhà cung cấp)` | Trực tiếp hoặc format UI |
| 5 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 6 | Mã lô | `field_root (Mã lô)` | Trực tiếp hoặc format UI |
| 7 | Lot lô NCC | `field_root (Lot lô NCC)` | Trực tiếp hoặc format UI |
| 8 | Giờ lấy mẫu | `time0 / create_time` | Định dạng HH:mm:ss |
| 9 | Số lượng nhập | `so_luong / quantity` | SUM() nếu gộp dòng |
| 10 | Số lượng mẫu | `so_luong / quantity` | SUM() nếu gộp dòng |
| 11 | Số lượng kiểm tra | `so_luong / quantity` | SUM() nếu gộp dòng |
| 12 | Số lượng OK | `so_luong / quantity` | SUM() nếu gộp dòng |
| 13 | Số lượng NG | `so_luong / quantity` | SUM() nếu gộp dòng |
| 14 | ĐVT | `field_root (ĐVT)` | Trực tiếp hoặc format UI |
| 15 | Tên chỉ tiêu | `field_root (Tên chỉ tiêu)` | Trực tiếp hoặc format UI |
| 16 | Item | `field_root (Item)` | Trực tiếp hoặc format UI |
| 17 | Giá trị tiêu chuẩn | `field_root (Giá trị tiêu chuẩn)` | Trực tiếp hoặc format UI |
| 18 | Min | `field_root (Min)` | Trực tiếp hoặc format UI |
| 19 | Max | `field_root (Max)` | Trực tiếp hoặc format UI |
| 20 | Khoảng FA min | `ma_kh / ten_kh` | JOIN dmkh |
| 21 | Khoảng FA max | `ma_kh / ten_kh` | JOIN dmkh |
| 22 | Vị trí đo | `field_root (Vị trí đo)` | Trực tiếp hoặc format UI |
| 23 | Dụng cụ đo | `field_root (Dụng cụ đo)` | Trực tiếp hoặc format UI |
| 24 | Số seri dụng cụ | `field_root (Số seri dụng cụ)` | Trực tiếp hoặc format UI |

---

### 66. Bảng kê chi tiết bài kiểm tra theo mã hàng
- **Phân hệ**: `QC`
- **Bảng vật lý trong DB**: `qc_baikiemtra_sp, dmvt`
- **Khóa liên kết / Logic gộp**: `Tiêu chuẩn kiểm tra theo từng mã sản phẩm.`
- **Ghi chú nghiệp vụ**: Thông số kích thước, ngoại quan yêu cầu.
- **Số lượng cột trên giao diện**: 23 cột

| STT | Cột hiển thị trên UI | Cột / Biểu thức DB tương ứng | Quy tắc xử lý / Gộp cột |
| :---: | :--- | :--- | :--- |
| 1 | STT | `ROW_NUMBER() OVER()` | Đánh số tự động |
| 2 | Mã vật tư | `field_root (Mã vật tư)` | Trực tiếp hoặc format UI |
| 3 | Mã công đoạn | `field_root (Mã công đoạn)` | Trực tiếp hoặc format UI |
| 4 | Mã bài kiểm tra | `field_root (Mã bài kiểm tra)` | Trực tiếp hoặc format UI |
| 5 | Xác nhận quy trình (Y/N) | `field_root (Xác nhận quy trình (Y/N))` | Trực tiếp hoặc format UI |
| 6 | Mã chỉ tiêu | `field_root (Mã chỉ tiêu)` | Trực tiếp hoặc format UI |
| 7 | Tên chỉ tiêu | `field_root (Tên chỉ tiêu)` | Trực tiếp hoặc format UI |
| 8 | Mã đơn vị đo lường | `field_root (Mã đơn vị đo lường)` | Trực tiếp hoặc format UI |
| 9 | Kiểu giá trị | `field_root (Kiểu giá trị)` | Trực tiếp hoặc format UI |
| 10 | Kiểu so sánh | `field_root (Kiểu so sánh)` | Trực tiếp hoặc format UI |
| 11 | Item | `field_root (Item)` | Trực tiếp hoặc format UI |
| 12 | Giá trị mặc định | `field_root (Giá trị mặc định)` | Trực tiếp hoặc format UI |
| 13 | Min | `field_root (Min)` | Trực tiếp hoặc format UI |
| 14 | Max | `field_root (Max)` | Trực tiếp hoặc format UI |
| 15 | Khoảng FA | `ma_kh / ten_kh` | JOIN dmkh |
| 16 | Khoảng FA min | `ma_kh / ten_kh` | JOIN dmkh |
| 17 | Khoảng FA max | `ma_kh / ten_kh` | JOIN dmkh |
| 18 | Vị trí đo | `field_root (Vị trí đo)` | Trực tiếp hoặc format UI |
| 19 | Dụng cụ đo | `field_root (Dụng cụ đo)` | Trực tiếp hoặc format UI |
| 20 | Số seri dụng cụ | `field_root (Số seri dụng cụ)` | Trực tiếp hoặc format UI |
| 21 | Tần suất đo | `field_root (Tần suất đo)` | Trực tiếp hoặc format UI |
| 22 | Ghi chú | `field_root (Ghi chú)` | Trực tiếp hoặc format UI |
| 23 | Lý do thay đổi | `field_root (Lý do thay đổi)` | Trực tiếp hoặc format UI |

---
