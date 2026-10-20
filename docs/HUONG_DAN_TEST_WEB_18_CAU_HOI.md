# Hướng dẫn Kiểm thử 18 Câu hỏi Nghiệp vụ Sales ERP trên Web (Open WebUI)

Tài liệu này cung cấp danh sách đầy đủ 18 câu hỏi trích xuất từ file [`sales_question.xlsx`](file:///home/admin/ai-stack/sales_question.xlsx) đã được bổ sung đầy đủ các **thông số kiểm thử thực tế** (Mã vật tư, Mã khách hàng, Mã khuôn, Số lệnh giao hàng, Khoảng thời gian đối soát và Ngày tham chiếu).

Người dùng chỉ cần **sao chép trực tiếp các câu prompt bên dưới** và dán vào ô chat trên giao diện web Open WebUI.

---

## Bảng tổng hợp thông số đối soát mẫu (Staging Dataset)

| Thông số | Giá trị thực tế sử dụng | Ý nghĩa |
|---|---|---|
| **Mã vật tư / thành phẩm (`ma_vt`)** | `QC7-5146-000` | Mã linh kiện kiểm thử trọng điểm |
| **Mã khách hàng (`ma_kh`)** | `KH0015` | Công ty TNHH Canon Việt Nam- Chi nhánh Thăng Long |
| **Mã khuôn (`ma_khuon`)** | `K_QC5-2919-000-V1` | Khuôn ép linh kiện `QC7-5146-000` |
| **Số lệnh giao hàng (`so_ct`)** | `001-2610-001811` | Chứng từ giao hàng gần nhất |
| **Khoảng ngày đối soát (`date_from` - `date_to`)** | `01/10/2026` đến `20/10/2026` | Kỳ kiểm toán tháng 10/2026 |
| **Ngày tham chiếu hiện tại (`reference_date`)** | `20/10/2026` | Mốc chốt số liệu tồn kho / bảng giá |

---

## Chi tiết 18 câu hỏi kiểm thử trên Web

### Nhóm 1: Cấu trúc sản phẩm (BOM) & Giá bán (Pricing)

#### Câu 1: Cấu trúc nhựa trong BOM
- **Câu hỏi gốc trong Excel:** *Mã hàng dùng nhựa gì?*
- **Câu prompt copy test:**
  ```text
  Mã hàng QC7-5146-000 dùng nhựa gì? Tra cứu theo định mức BOM đang có hiệu lực tính đến ngày 20/10/2026.
  ```
- **Kết quả kỳ vọng (Expected Answer):**
  - Nhựa: `PS-576D` (Tên: *HIPS 576H GR21 PSMT VE0271-33 Nu-0215 Dim black MBB3%*).
  - Định mức: `0,026 KG`.
  - BOM Version: `QC7-5146-000-1.0`, hiệu lực: `01/01/2023 – 02/11/2032`.

#### Câu 2: MOQ và Bảng giá hiện hành
- **Câu hỏi gốc trong Excel:** *MOQ báo giá của mã hàng là bao nhiêu? Giá áp dụng hiện tại là bao nhiêu?*
- **Câu prompt copy test:**
  ```text
  MOQ báo giá của mã hàng QC7-5146-000 là bao nhiêu? Giá áp dụng hiện tại tính đến ngày 20/10/2026 là bao nhiêu?
  ```
- **Kết quả kỳ vọng (Expected Answer):**
  - Khách hàng áp dụng: `KH0015` (Canon Thăng Long).
  - MOQ tối thiểu (`sl_min`): `1 PCS`.
  - Giá áp dụng: `0,08563 USD/PCS` (ngoại tệ USD).
  - Thời gian hiệu lực: `25/09/2026 – 31/12/2026`, trạng thái đang áp dụng (`status = 1`).

---

### Nhóm 2: Xuất kho bán hàng & Doanh thu (Sales & Delivery)

#### Câu 3: Lot giao gần nhất
- **Câu hỏi gốc trong Excel:** *Lot giao gần nhất của mã hàng là khi nào? Số lượng bao nhiêu?*
- **Câu prompt copy test:**
  ```text
  Lot giao gần nhất của mã hàng QC7-5146-000 tính đến ngày 20/10/2026 là khi nào? Số lượng bao nhiêu?
  ```
- **Kết quả kỳ vọng (Expected Answer):**
  - Ngày phiếu xuất gần nhất: `20/10/2026`.
  - Mã Lot: Trên chứng từ xuất bán mới nhất này, mã lot thực tế trên hệ thống ERP đang để trống (trả về rõ tình trạng dữ liệu thay vì bịa mã).
  - Nêu rõ số chứng từ và số lượng xuất tương ứng trên phiếu xuất ngày 20/10/2026.

#### Câu 4: Tổng sản lượng và doanh thu xuất bán
- **Câu hỏi gốc trong Excel:** *Tổng số lượng xuất hàng của mã hàng từ thời điểm này đến thời điểm này là bao nhiêu? Và doanh thu?*
- **Câu prompt copy test:**
  ```text
  Tổng số lượng xuất hàng của mã hàng QC7-5146-000 từ ngày 01/10/2026 đến hết ngày 20/10/2026 là bao nhiêu? Và doanh thu tương ứng?
  ```
- **Kết quả kỳ vọng (Expected Answer):**
  - Tổng số bản ghi phiếu xuất: `304` dòng chứng từ.
  - Tổng số lượng xuất: `83.100 PCS`.
  - Doanh thu / tiền hàng: Thể hiện đúng tổng tiền hàng tương ứng trong kỳ đối soát.

#### Câu 5: Thông tin Khách hàng sở hữu mã hàng
- **Câu hỏi gốc trong Excel:** *Mã hàng này của khách hàng nào*
- **Câu prompt copy test:**
  ```text
  Mã hàng QC7-5146-000 này là của khách hàng nào?
  ```
- **Kết quả kỳ vọng (Expected Answer):**
  - Mã khách hàng: `KH0015`.
  - Tên khách hàng: **Công ty TNHH Canon Việt Nam- Chi nhánh Thăng Long**.

---

### Nhóm 3: Nhập kho & Kế hoạch sản xuất / Dự báo (Receipts & Forecast)

#### Câu 6: Lịch sử nhập kho thành phẩm
- **Câu hỏi gốc trong Excel:** *Mã hàng được nhập kho khi nào? Từ kho nào sang? Số lượng nhập là bao nhiêu? Người nhập là ai?*
- **Câu prompt copy test:**
  ```text
  Mã hàng QC7-5146-000 được nhập kho khi nào từ ngày 01/10/2026 đến hết ngày 20/10/2026? Từ kho nào sang? Số lượng nhập là bao nhiêu? Người nhập là ai?
  ```
- **Kết quả kỳ vọng (Expected Answer):**
  - Tổng phát sinh nhập kho: `412` bản ghi trong sổ nhập kho `ct70`.
  - Tổng số lượng nhập: `474.140 PCS`.
  - Các kho xuất chuyển sang: `KHO_TAIMAY`, `KHOTP00`, `KHOTP02`.
  - Người lập/nhập chứng từ tiêu biểu: `KHO2`, `KHO3`, `KHO5`, `DUC0223`...

#### Câu 7: Biến động Kế hoạch DO và FCST
- **Câu hỏi gốc trong Excel:** *So sánh biến động DO, FCST hiện tại và quá khứ ( tăng, giảm)?*
- **Câu prompt copy test:**
  ```text
  So sánh biến động DO, FCST hiện tại và quá khứ (tăng, giảm) của mã hàng QC7-5146-000 tính đến ngày 20/10/2026?
  ```
- **Kết quả kỳ vọng (Expected Answer):**
  - Dữ liệu kế hoạch: Ghi nhận số lượng `1.200 PCS` trong bảng kế hoạch `mfkhsx_po_fc`.
  - Giải thích ranh giới ERP: Hệ thống ERP hiện tại lưu theo đợt tính toán (snapshot) chứ chưa lưu lịch sử phiên bản FCST quá khứ để tính tăng/giảm delta trực tiếp.

---

### Nhóm 4: Quy cách đóng gói & Hồ sơ khuôn (Packaging & Molds)

#### Câu 8: Quy cách đóng gói và Quy đổi tồn kho
- **Câu hỏi gốc trong Excel:** *Quy cách đóng gói chi tiết của mã hàng? Và quy tồn kho hiện tại theo quy cách đóng gói là bao nhiêu vật tư?*
- **Câu prompt copy test:**
  ```text
  Quy cách đóng gói chi tiết của mã hàng QC7-5146-000? Và quy đổi tồn kho hiện tại theo quy cách đóng gói tính đến ngày 20/10/2026 là bao nhiêu?
  ```
- **Kết quả kỳ vọng (Expected Answer):**
  - Quy cách: `60 PCS/thùng` (Mã thùng: `BGTD0070`), `10 PCS/khay` (Mã khay: `BGKP0012`).
  - Tồn kho sổ sách: `6.040 PCS`.
  - Quy đổi: Tương đương `100 thùng` (còn dư lẻ 40 PCS) hoặc `604 khay`.

#### Câu 9: Số shot đã chạy và Tuổi thọ khuôn
- **Câu hỏi gốc trong Excel:** *Khuôn này đã chạy được bao nhiêu shots? Theo demand của khách hàng thì dự kiến khi nào hết tuổi thọ khuôn?*
- **Câu prompt copy test:**
  ```text
  Khuôn K_QC5-2919-000-V1 đã chạy được bao nhiêu shots? Theo demand của khách hàng thì dự kiến khi nào hết tuổi thọ khuôn?
  ```
- **Kết quả kỳ vọng (Expected Answer):**
  - Tổng số shot đã chạy lũy kế: `1.669.051 shot`.
  - Số shot bảo hành: `1.000.000 shot` (thực tế đã chạy vượt mức bảo hành ban đầu).
  - Dự báo hết hạn: ERP chưa có công thức tự động nội suy ngày hết hạn theo demand khách hàng nếu không có cấu hình số cavity và lịch giao chi tiết.

---

### Nhóm 5: So sánh kỳ & Chi tiết khuôn tồn kho (Comparisons & Mold Stock)

#### Câu 10: So sánh doanh số 2 kỳ liên tiếp
- **Câu hỏi gốc trong Excel:** *So sánh doanh thu của mã hàng, khách hàng?*
- **Câu prompt copy test:**
  ```text
  So sánh sản lượng và doanh thu xuất bán của mã hàng QC7-5146-000 cho khách hàng KH0015 giữa kỳ 01/09/2026 - 20/09/2026 và kỳ 01/10/2026 - 20/10/2026?
  ```
- **Kết quả kỳ vọng (Expected Answer):**
  - Kỳ 01/09 - 20/09: `84.840 PCS` (290 dòng phiếu xuất).
  - Kỳ 01/10 - 20/10: `83.100 PCS` (304 dòng phiếu xuất).
  - Biến động: Giảm `1.740 PCS` (-2.05%) giữa 2 kỳ đối chiếu.

#### Câu 11: Tồn kho tem thành phẩm theo từng khuôn (Die No)
- **Câu hỏi gốc trong Excel:** *Mã hàng có tồn kho hiện tại bao gồm của những khuôn nào? Số lượng tồn kho cụ thể của từng khuôn?*
- **Câu prompt copy test:**
  ```text
  Mã hàng QC7-5146-000 có tồn kho tem thành phẩm hiện tại bao gồm của những khuôn (die) nào? Số lượng tồn kho cụ thể của từng khuôn tính đến 20/10/2026?
  ```
- **Kết quả kỳ vọng (Expected Answer):**
  - Tồn kho tem thành phẩm (`intem_log`) gồm:
    - Khuôn / Die `V1`: `15.300 PCS`.
    - Khuôn / Die `V2`: `1.120 PCS`.
  - Tổng tồn kho tem thành phẩm: `16.420 PCS`.

---

### Nhóm 6: Lịch sử Đơn hàng & Lệnh giao hàng (Orders & Shipping)

#### Câu 12: Đơn hàng bán trong quá khứ
- **Câu hỏi gốc trong Excel:** *Cung cấp data đơn hàng quá khứ ( chỉ định thời điểm) của khách hàng?*
- **Câu prompt copy test:**
  ```text
  Cung cấp dữ liệu đơn hàng bán quá khứ của khách hàng KH0015 từ ngày 01/10/2026 đến hết ngày 20/10/2026?
  ```
- **Kết quả kỳ vọng (Expected Answer):**
  - Tổng số đơn hàng bán phát sinh trong kỳ: `2.109` dòng đơn hàng.
  - Tổng khối lượng đặt: `3.654.485 PCS`.
  - Kèm danh sách các đơn hàng tiêu biểu (Mã chứng từ, ngày đặt, mã hàng, số lượng).

#### Câu 13: Tiến độ hoàn thiện Lệnh giao hàng
- **Câu hỏi gốc trong Excel:** *Lệnh giao hàng được hoàn thiện khi nào?*
- **Câu prompt copy test:**
  ```text
  Lệnh giao hàng số 001-2610-001811 được hoàn thiện khi nào? Tình trạng hiện tại ra sao?
  ```
- **Kết quả kỳ vọng (Expected Answer):**
  - Thời điểm tạo lập: `19:28:20` ngày `19/10/2026`.
  - Trạng thái: `status = 1` (*Chờ chỉ thị lô*), chứng từ chưa hoàn thiện xuất kho vật lý.

---

### Nhóm 7: Tồn kho sổ sách & Trạng thái chất lượng (Ledger & QC)

#### Câu 14: Tồn kho sổ sách cuối kỳ
- **Câu hỏi gốc trong Excel:** *Tồn kho hiện tại của mã hàng là bao nhiêu?*
- **Câu prompt copy test:**
  ```text
  Tồn kho sổ sách hiện tại của mã hàng QC7-5146-000 là bao nhiêu tính đến ngày 20/10/2026?
  ```
- **Kết quả kỳ vọng (Expected Answer):**
  - Tồn kho sổ sách cuối kỳ (bảng `cdvt`): `5.620 PCS`.
  - Phân biệt rõ giữa tồn kho sổ sách kế toán (`5.620 PCS`) và tồn kho thực tế quét tem (`16.420 PCS`).

#### Câu 15: Kiểm tra Lot khóa / Khoanh vùng NG
- **Câu hỏi gốc trong Excel:** *Tồn kho thành phẩm có lot nào đang ở trạng thái khóa hoặc khoanh vùng NG không?*
- **Câu prompt copy test:**
  ```text
  Tồn kho thành phẩm của mã hàng QC7-5146-000 có lot nào đang ở trạng thái khóa hoặc khoanh vùng NG không tính đến ngày 20/10/2026?
  ```
- **Kết quả kỳ vọng (Expected Answer):**
  - Trạng thái kiểm tra: Toàn bộ tem hoạt động đều có `status_qc = 3` (*3 - OK / Đạt chất lượng*).
  - Kết luận: Không có lot hay tem nào bị khóa (`status_qc = 5` - NG) hoặc chờ xử lý (`status_qc = 6`).

---

### Nhóm 8: Kiểm tra dữ liệu bất thường & Bù hàng NG (Anomalies & Replacements)

#### Câu 16: Kiểm tra mã hàng chưa link giá chuẩn
- **Câu hỏi gốc trong Excel:** *Khách hàng này có mã hàng nào chưa link được giá trên ERP không?*
- **Câu prompt copy test:**
  ```text
  Khách hàng KH0015 có mã hàng nào trong các đơn hàng từ 01/10/2026 đến 20/10/2026 chưa link được giá trên ERP không?
  ```
- **Kết quả kỳ vọng (Expected Answer):**
  - Phát hiện mã hàng: `QM5-1557-000` trên các dòng đơn hàng bán có `gia_chuan = 0`.
  - Kết luận: Mã này chưa được thiết lập giá chuẩn trên bảng giá ERP.

#### Câu 17: Tra cứu Mã khách hàng theo Tên công ty
- **Câu hỏi gốc trong Excel:** *Khách hàng này có mã khách hàng là gì?*
- **Câu prompt copy test:**
  ```text
  Khách hàng Công ty TNHH Canon Việt Nam- Chi nhánh Thăng Long có mã khách hàng là gì trên hệ thống ERP?
  ```
- **Kết quả kỳ vọng (Expected Answer):**
  - Mã khách hàng: `KH0015` (trong danh mục khách hàng `dmkh`).

#### Câu 18: Đối soát Giao bù NG & Nhận lại hàng lỗi
- **Câu hỏi gốc trong Excel:** *Số lượng giao bù NG mã hàng này từ thời điểm này đến thời điểm này là bao nhiêu? Số lượng NG đã nhận lại? Số lượng chưa giao bù và chưa nhận về là bao nhiêu?*
- **Câu prompt copy test:**
  ```text
  Số lượng giao bù NG mã hàng QC7-5146-000 từ ngày 01/10/2026 đến hết ngày 20/10/2026 là bao nhiêu? Số lượng NG đã nhận lại? Số lượng chưa giao bù và chưa nhận về là bao nhiêu?
  ```
- **Kết quả kỳ vọng (Expected Answer):**
  - Kết quả kiểm tra: Trong kỳ không có phát sinh lệnh giao hàng bù NG (mã giao dịch `10` trong `ph96/ct96`).
  - Số lượng giao bù = `0`, Số lượng nhận lại = `0`.
