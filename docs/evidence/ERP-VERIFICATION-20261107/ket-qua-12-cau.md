# BÁO CÁO NGHIỆM THU TỔNG THỂ 12 CÂU NGHIỆP VỤ ERP / MES (07/11/2026)

## 1. TỔNG QUAN

- **Mục tiêu:** Xây dựng và nghiệm thu hệ thống truy vấn tự nhiên cho mô hình `HTMP ERP` (`htmp-nhanh`) trên Open WebUI, trả lời chính xác 100% 12 nhóm nghiệp vụ cốt lõi từ dữ liệu thực tế của hệ thống ERP 3S và MES HTMP.
- **Môi trường DB:** PostgreSQL 10.16 (`10.0.6.2:5410/3SERP_HTMP_DATA`), kết nối read-only có transaction an toàn (`conn.rollback()`).
- **Môi trường WebUI:** Container `open-webui` (`http://127.0.0.1:80` / `http://192.168.31.10:8080`).

---

## 2. BẢNG SO SÁNH TRƯỚC VÀ SAU CẢI TIẾN

| STT | Nghiệp vụ | Câu hỏi kiểm thử | Hiện trạng ban đầu (Baseline) | Kết quả sau cải tiến | Trạng thái |
|:---:|:---|:---|:---|:---|:---:|
| **01** | **Bán hàng** | *Cho tôi danh sách đơn hàng bán của khách hàng KH0047 trong tháng 10/2026* | Lỗi `ModuleNotFoundError: No module named 'functions'` | Trả danh sách đơn hàng (`ct64`/`ph64`) chi tiết theo từng số CT, ngày CT, mã VT, số lượng, đơn giá, thành tiền | **PASSED** |
| **02** | **Giá bán** | *check cho chị giá bán của mã hàng 156279430* | Lỗi không tìm thấy giá | Trích xuất chính xác từ `dmbanggiact`: 12,105 VND/PCS (KH: ANTOLIN), hiệu lực đến 31/12/2026 | **PASSED** |
| **03** | **Tiến độ giao** | *Đơn hàng và tiến độ giao của mã QC7-5146-000 thế nào?* | Không có thông tin tiến độ giao | Gọi thủ tục chuẩn ERP `sobctiendogh`: Tổng đặt 167,440 PCS, Đã giao 154,640 PCS, Đúng hạn 149,100 PCS, Giao chậm 5,540 PCS, Còn lại 7,780 PCS, kèm danh sách đơn chi tiết | **PASSED** |
| **04** | **Mua hàng** | *Đơn mua hàng từ nhà cung cấp NCC0220 trong tháng 10/2026 gồm những đơn nào?* | Lỗi tra cứu do thiếu tham số vật tư bắt buộc | Trả toàn bộ danh sách PO từ `ct94`/`ph94` của nhà cung cấp NCC0220 theo số CT, ngày CT, số lượng | **PASSED** |
| **05** | **Giá mua** | *Lịch sử đơn giá mua của vật tư PS-576D gần đây ra sao?* | Lỗi tra cứu giá mua | Trả lịch sử đơn giá mua gần nhất từ `ct94` (NCC0003 - CÔNG TY DAINICHI COLOR VIỆT NAM...) | **PASSED** |
| **06** | **Tồn kho** | *Tồn kho của mã 75577-BZ010 theo từng kho là bao nhiêu?* | Lỗi `ModuleNotFoundError` | Tính toán số dư đầu kỳ (`cdvt`) + biến động (`ct70`): Kho KHOTP00 tồn 212 SET | **PASSED** |
| **07** | **Thẻ kho** | *Cho tôi thẻ kho của vật tư QC7-5146-000 tại KHOTP00 từ 01/10 đến 07/10/2026* | Bị nhầm sang tra cứu tồn tức thời | Kích hoạt công cụ `lookup_stock_card`: Tổng nhập 17,640 PCS, Tổng xuất 21,060 PCS, bảng chi tiết chứng từ PNF, PXB | **PASSED** |
| **08** | **Dừng máy MES** | *Tổng hợp thời gian dừng máy theo nguyên nhân trong tháng 10/2026* | Trả lời sai "không có dữ liệu" do nhầm tháng thành mã máy | Trích xuất bảng `mes_oi_stop_line` + `dmnndungmay`: Kế hoạch 3,186 lần (164,448 phút), Vệ sinh khuôn 2,312 lần (46,195 phút), Dính dầu 857 lần (43,477 phút)... | **PASSED** |
| **09** | **Sản xuất MES** | *Thống kê thời gian dừng máy sự cố của máy DUC-0201 trong tháng 10/2026* | Trả lời sai "không có dữ liệu" | Phân tích 305 lượt dừng máy của DUC-0201 trong tháng 10/2026 (5,406.1 phút), phân loại theo biến dạng, kế hoạch, bavia khuôn... | **PASSED** |
| **10** | **BOM** | *Theo BOM mã QC7-5146-000 sử dụng loại nhựa nào và định mức bao nhiêu?* | Bị chuyển sai sang tra cứu số shot khuôn | Kích hoạt công cụ `lookup_bom`: Mã hạt nhựa `PS-576D`, định mức tiêu hao `0.026 KG` | **PASSED** |
| **11** | **Khuôn MES** | *Khuôn của mã QC7-5146-000 đã dập bao nhiêu shot và giới hạn bảo hành là bao nhiêu?* | Lỗi cột `ma_vt` không tồn tại trong `dmhosokhuonsp` | Sửa join trên `ma_sp`: Khuôn `K_QC5-2919-000-V1` (14HI202), đã dập `1,721,342` shot, bảo hành `1,000,000` shot | **PASSED** |
| **12** | **Chất lượng IQC** | *Báo cáo đánh giá chất lượng hàng mua theo nhà cung cấp trong tháng 10/2026* | Chưa có công cụ chuyên biệt | Kích hoạt `lookup_incoming_quality` (`phiqc` + `dmkh`): Tổng 310 lô, Đạt 268 lô (86.5%), bảng chi tiết theo NCC | **PASSED** |

---

## 3. CÁC NÂNG CẤP KỸ THUẬT QUAN TRỌNG ĐÃ TRIỂN KHAI

1. **Khử phụ thuộc Module nội bộ (`ModuleNotFoundError`):**
   - Độc lập hóa hoàn toàn `erp_ai/native_tools.py`, tự quản lý cấu hình kết nối, chuẩn hóa dữ liệu số và timeout, không phụ thuộc vào cấu trúc thư mục ngoài container.
   - Đồng bộ hóa công cụ `htmp_postgres_query.py` và cập nhật OpenAPI spec (`webui.db`) trực tiếp trong Open WebUI.

2. **Reverse-Engineering Nghiệp vụ Chuyên sâu ERP 3S & MES:**
   - **Báo cáo tiến độ giao hàng (`sobctiendogh`):** Tích hợp stored procedure gốc của ERP 3S với mô hình transaction `autocommit=False` + `conn.rollback()`, cho phép tính toán chính xác số lượng đặt, số lượng đã xuất hóa đơn, số lượng còn lại, giao đúng kế hoạch và giao chậm.
   - **Thẻ kho chi tiết (`lookup_stock_card`):** Tách thành công cụ độc lập truy vấn trực tiếp bảng sổ cái kho `ct70`, phân loại phiếu nhập thành phẩm (PNF) và phiếu xuất bán (PXB).
   - **Cấu trúc BOM (`lookup_bom`):** Tách riêng truy vấn cấu trúc định mức hạt nhựa từ `mfbom_material` kết hợp `dmvt`, loại bỏ triệt để hiện tượng LLM nhầm lẫn BOM sang tra cứu khuôn.
   - **Dừng máy MES (`lookup_mes_downtime`):** Tự động tính toán khoảng thời gian từ `(end_time - create_time)` trên 428,000+ bản ghi dừng chuyền `mes_oi_stop_line`, map với danh mục lỗi dừng máy `dmnndungmay`.
   - **Đánh giá IQC (`lookup_incoming_quality`):** Tự động thống kê số lô kiểm tra, số lô OK/NG, tỷ lệ đạt theo từng nhà cung cấp từ bảng `phiqc`.

3. **Sửa lỗi Phân tích Ngày tháng (Date Range Parsing):**
   - Xử lý triệt để lỗi Regex khiến các chuỗi ISO `YYYY-MM-DD` bị cắt nhầm thành `YYYY-DD-MM` gây lỗi `DatetimeFieldOverflow: date/time field value out of range`.
   - Chuẩn hóa thứ tự ưu tiên nhận dạng: ISO Date -> Dải ngày cụ thể (DD/MM đến DD/MM/YYYY) -> Tháng cụ thể (tháng 10/2026) -> Mặc định.

4. **Bảo toàn Hệ thống Sản xuất (Production Safety):**
   - Giữ nguyên trạng 100% các nhánh GPT/API và file patches không thuộc phạm vi công việc.
   - Mọi thao tác truy vấn DB tuân thủ nghiêm ngặt cấm ghi/sửa dữ liệu (`READ ONLY` hoặc `ROLLBACK`).

