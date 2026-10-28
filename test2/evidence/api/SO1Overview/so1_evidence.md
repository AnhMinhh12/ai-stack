# Bằng Chứng Thực Nghiệm Màn Hình SO1 (Đơn Hàng / Hợp Đồng) — Phiên Bản Cập Nhật Bàn Giao

- **Trạng thái màn hình (Screen State)**: `SO1Overview` (Mã chứng từ: `SO1`)
- **Đường dẫn (URL)**: `http://10.0.6.2:1004/Solution/ERP/#/SO/SO1`
- **Thời điểm xác minh**: `2026-10-27T09:45:00+07:00`
- **Tài khoản**: `IT.ERP` / Đơn vị: `001 - HTMP QM`
- **Ảnh chụp giao diện bàn giao (Đã che dữ liệu nhạy cảm)**: [`so1_grid_screenshot_redacted.png`](file:///C:/Users/it07/Downloads/test2/evidence/api/SO1Overview/so1_grid_screenshot_redacted.png)
  *(Lưu ý bảo mật: Bản chụp thô chứa tên khách hàng, địa chỉ và người liên hệ thực tế đã được đưa vào `.gitignore` để nghiêm cấm chia sẻ hoặc commit)*

---

## 1. Kết Quả Xác Minh Thực Nghiệm

Dựa trên ảnh chụp thực tế [`so1_grid_screenshot_redacted.png`](file:///C:/Users/it07/Downloads/test2/evidence/api/SO1Overview/so1_grid_screenshot_redacted.png) và phiên làm việc trình duyệt live:

### 1.1 Đã Xác Minh Trên Giao Diện UI (`UI_RENDERED_LIVE`)
- **Tiêu đề trang (Page Title)**: `Đơn hàng (Hợp đồng)`
- **Tiêu đề khối giao diện (Heading)**: `ĐƠN HÀNG (HỢP ĐỒNG)`
- **Tổng số bản ghi hiển thị trên giao diện**: `579 110` (nằm cạnh tiêu đề khối)
- **Các control tìm kiếm & lọc trên UI**: `Từ ngày CT` / `Đến ngày CT`, `Từ số CT` / `Đến số CT`, `Từ tổng SL`, `Từ tổng tiền`, `Mã ĐVCS` (mặc định: `001`), `Mã vật tư`, `Số CT báo giá`, checkbox `Tìm kiếm với giá trị bằng 0`.
- **10 Cột hiển thị thực tế trên Grid**:
  1. `#` (Cột số thứ tự / chọn dòng)
  2. `Trạng thái`
  3. `Ngày CT`
  4. `Số CT`
  5. `Mã giao dịch`
  6. `Tên giao dịch`
  7. `Số PO KH`
  8. `Mã khách hàng`
  9. `Tên khách hàng`
  10. `Địa chỉ`
  11. `Người liên lạc`
- **Dữ liệu dòng**: Hiển thị thực tế 20 dòng bản ghi trên trang đầu tiên của grid.

### 1.2 Chưa Xác Minh API / Database (Giữ nguyên `UI_CONFIG_LIVE` / `UNVERIFIED`)
Mặc dù nhãn cột và dữ liệu đã hiển thị trên UI, các thành phần kỹ thuật sau **chưa có bằng chứng độc lập từ API hoặc Database**, do đó trong [`field-map.csv`](file:///C:/Users/it07/Downloads/test2/mapping/field-map.csv) tiếp tục giữ nguyên ở mức `UI_CONFIG_LIVE` hoặc `UNVERIFIED`:
- **Chưa xác minh API Response thô**: Chưa có file raw response / file HAR đã che dữ liệu được lưu trữ độc lập để đối chiếu schema JSON thực tế.
- **Chưa xác minh Database Catalog**: Tên bảng `ph`, `dmkh`, `sys_dmtt` và các khóa nối `ph.status = sys_dmtt.status`, `ph.ma_kh = dmkh.ma_kh` mới chỉ dựa trên metadata cấu hình và bundle client, chưa có catalog hay query SELECT từ database để chứng minh (chưa đạt `DB_VERIFIED`).
- **Chưa xác minh Detail Tables**: Các bảng chi tiết `ct64` (mặt hàng), `ctkhgh` (giao hàng), `ctck20` (chiết khấu) mới chỉ ghi nhận từ form HTML `SO1Overview.html`, chưa mở chứng từ chi tiết live để ghi nhận dữ liệu thực.
- **Chưa xác minh Công thức**: Công thức tính hạn thanh toán theo `han_tt` / `ngay_cd` và tra giá qua `GetMainItemPriceByDate` mới là code JavaScript client, chưa có đối soát SQL.

---

## 2. Tiêu Chí Để Đạt Mức `DATA_API_LIVE`, `DB_VERIFIED` và `RECONCILED`

1. **`DATA_API_LIVE`**: Bắt được network request `GetData` thực tế từ browser/CDP và lưu file raw response đã che PII vào `evidence/api/SO1Overview/response_raw_redacted.json`.
2. **`DB_VERIFIED`**: Kết nối SQL chỉ đọc để trích xuất định nghĩa bảng `ph`, `dmkh`, `sys_dmtt`, view và các ràng buộc khóa ngoại.
3. **`RECONCILED`**: Chọn 3 bản ghi chứng từ cụ thể trên `SO1` để chứng minh:
   ```text
   Giá trị hiển thị trên Web Grid == Trường dữ liệu trong API JSON Response == Kết quả câu lệnh SQL SELECT trực tiếp
   ```
   Chỉ khi đối soát khớp hoàn toàn cả 3 nguồn trên thì mới được nâng cấp thành `RECONCILED`.
