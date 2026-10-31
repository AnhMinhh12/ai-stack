# BỘ CÂU HỎI KIỂM THỬ TRÍ TUỆ NHÂN TẠO ERP & TỔNG HỢP BÁO CÁO (HTMP AI STACK)

> **Cập nhật:** Ngày 29/10/2026 (Đã kiểm chứng và xác thực 100% dữ liệu thực tế)  
> **Phạm vi áp dụng:** Open WebUI Chat / Model `htmp-nhanh` (`Qwen2.5-14B`) kết nối cơ sở dữ liệu `3SERP_HTMP_DATA`  
> **Tính năng tự động kích hoạt:**
> - 📊 **Rich UI:** Tự động sinh bảng dữ liệu, biểu đồ trực quan (Cột / Đường / Tròn) với nền trong suốt hòa vào khung chat.
> - 🔄 **Chuyển đổi biểu đồ:** Nút bấm linh hoạt chuyển đổi qua lại giữa biểu đồ Cột, Đường và Tròn.
> - 📥 **Xuất báo cáo:** Nút tải file Excel (`.xlsx`) và CSV trực tiếp từ giao diện chat.
> - ⚖️ **Đối soát & So sánh kỳ:** Hỗ trợ so sánh độc lập giữa 2 kỳ phát sinh và đối soát cân đối Đơn đặt (SO) vs Thực xuất (HDA).

---

## Hướng dẫn sử dụng
1. Mở giao diện Open WebUI trên trình duyệt (`http://<ip-server>:80` hoặc domain nội bộ).
2. Chọn mô hình AI (hoặc Model Profile đã tích hợp công cụ tra cứu ERP).
3. **Sao chép (Copy) trực tiếp các câu hỏi bên dưới** và dán vào ô chat để kiểm thử.

---

## PHẦN 1: BỘ CÂU HỎI TỔNG HỢP BÁO CÁO (AGGREGATED & VISUAL REPORTS)
*Các câu hỏi nhóm này trả về dữ liệu tổng hợp nhiều dòng, tự động kích hoạt **Bảng dữ liệu + Biểu đồ trực quan (Cột / Đường / Tròn) + Nút tải Excel/CSV**.*

### 1. Báo cáo Tồn kho & Vật tư (Inventory Reports)
1. **Top vật tư tồn kho lớn nhất:**
   ```text
   Cho tôi xem báo cáo top 10 vật tư có số lượng tồn kho lớn nhất hiện tại
   ```
   *(Kỳ vọng: Bảng tổng hợp mã VT, tên VT, ĐVT, số lượng tồn + Biểu đồ Cột/Tròn tỷ trọng + Nút tải Excel)*

2. **Tồn kho phân bổ theo từng kho:**
   ```text
   Tổng hợp số lượng tồn kho phân bổ theo từng kho hàng trong hệ thống
   ```
   *(Kỳ vọng: So sánh tồn kho giữa Kho Nguyên vật liệu, Kho Thành phẩm, Kho Tạimáy...)*

3. **Báo cáo biến động xuất nhập tồn theo ngày:**
   ```text
   Báo cáo tổng hợp số lượng nhập kho và xuất kho theo từng ngày từ ngày 01/10/2026 đến ngày 20/10/2026
   ```
   *(Kỳ vọng: Bảng dữ liệu chuỗi thời gian + Biểu đồ Đường thể hiện biến động theo ngày)*

---

### 2. Báo cáo Bán hàng & Đơn hàng (Sales & Delivery Reports)
4. **Top khách hàng theo số lượng đặt hàng:**
   ```text
   Cho tôi báo cáo top khách hàng có số lượng đặt hàng lớn nhất trong các đơn hàng bán gần đây
   ```
   *(Kỳ vọng: Bảng thống kê mã KH, tên KH, tổng số lượng đặt + Biểu đồ Cột/Tròn)*

5. **Báo cáo sản lượng xuất bán theo khách hàng:**
   ```text
   Tổng hợp sản lượng xuất kho bán hàng cho các khách hàng từ ngày 01/10/2026 đến hết ngày 20/10/2026
   ```
   *(Kỳ vọng: Thống kê sản lượng giao cho các đối tác lớn như Canon KH0015, Tohoku Pioneer KH0049, Anam KH0047...)*

6. **Báo cáo tiến độ giao hàng mã linh kiện máy in:**
   ```text
   Tổng hợp số lượng xuất kho bán hàng của mã hàng QC7-5146-000 theo từng ngày xuất từ ngày 01/10/2026 đến ngày 20/10/2026
   ```
   *(Kỳ vọng: Biểu đồ đường/cột thể hiện 304 lượt xuất với tổng 83.100 PCS)*

---

### 3. Báo cáo Mua hàng & Nhà cung cấp (Procurement & Supplier Reports)
7. **Báo cáo nhà cung cấp phát sinh đơn mua nhiều nhất:**
   ```text
   Tổng hợp số lượng đơn hàng mua và tổng số lượng vật tư đặt mua theo từng nhà cung cấp gần đây
   ```
   *(Kỳ vọng: So sánh sản lượng mua giữa các nhà cung cấp như Hungtech NCC0220...)*

8. **Báo cáo lịch sử giá mua của vật tư:**
   ```text
   Tổng hợp lịch sử các lần đặt mua, đơn giá mua thấp nhất, cao nhất và giá bình quân của mã nhựa PS-576D
   ```
   *(Kỳ vọng: Bảng đối soát chi tiết các lần mua + so sánh đơn giá mua qua các đợt)*

---

### 4. Báo cáo Quản lý Sản xuất & Chất lượng MES (Production & Quality Reports)
9. **Báo cáo tổng hợp phế phẩm (NG) theo dòng máy / line:**
   ```text
   Báo cáo tổng hợp số lượng sản phẩm lỗi NG theo từng máy sản xuất trong các ca làm việc gần đây
   ```
   *(Kỳ vọng: Biểu đồ Cột/Tròn phân tích tỷ lệ NG giúp ban giám đốc phát hiện máy có vấn đề)*

10. **Báo cáo phân loại lỗi sản xuất:**
    ```text
    Tổng hợp số lượng lỗi sản phẩm theo từng mã lỗi và nguyên nhân lỗi trong bảng kê xác nhận NG
    ```
    *(Kỳ vọng: Biểu đồ Pareto/Cột top nguyên nhân lỗi phế phẩm)*

11. **Báo cáo thời gian dừng máy (Downtime):**
    ```text
    Báo cáo tổng số phút dừng máy theo từng nguyên nhân dừng chuyền trong bảng kê stop line gần đây
    ```
    *(Kỳ vọng: Phân tích nguyên nhân dừng chuyền: sự cố khuôn, chờ vật tư, bảo trì...)*

12. **Báo cáo tiến độ Work Order (Lệnh sản xuất):**
    ```text
    Tổng hợp số lượng kế hoạch sản xuất theo từng Work Order trong bảng điều độ sản xuất gần đây
    ```
    *(Kỳ vọng: Bảng điều độ WO, mã máy, mã khuôn, số lượng kế hoạch và thời gian thực hiện)*

---

## PHẦN 2: BỘ CÂU HỎI TRA CỨU NGẪU NHIÊN THEO THỰC TẾ HỆ THỐNG (RANDOM AD-HOC QUERIES)
*Bộ câu hỏi kiểm tra độ nhạy của AI khi người dùng hỏi ngắn gọn, hỏi nhanh hoặc hỏi mã chứng từ cụ thể.*

### 1. Tra cứu Đơn hàng bán (SO) & Xuất kho (HDA)
13. `Cho tôi xem bảng kê đơn hàng bán gần đây nhất`
14. `Bảng kê đơn hàng bán của khách hàng mã KH0047`
15. `Tra cứu chi tiết đơn hàng bán số 001-2610-010164`
16. `Tìm kiếm các đơn hàng bán có chứa mã hàng VGL1A416`
17. `Bảng kê phiếu xuất kho bán hàng phát sinh ngày hôm nay`
18. `Bảng kê các phiếu xuất bán cho khách hàng mã KH0049`
19. `Xem chi tiết phiếu xuất kho bán hàng số 001-2610-002643`
20. `Lot giao gần nhất của mã hàng QC7-5146-000 là khi nào và số lượng bao nhiêu?`

### 2. Tra cứu Mua hàng (PO) & Báo giá NCC
21. `Bảng kê đơn hàng mua gần đây nhất của công ty`
22. `Bảng kê đơn hàng mua của nhà cung cấp mã NCC0220`
23. `Tra cứu đơn hàng mua số 001-2610-000702`
24. `Mã hàng PS-576D đã mua bao nhiêu lần và giá mua gần nhất là bao nhiêu?`
25. `Kiểm tra trạng thái duyệt giá và báo giá nhà cung cấp của mã vật tư PS-576D`

### 3. Tra cứu Kho vận & Điều chuyển nội bộ
26. `Bảng kê phiếu nhập kho nội bộ từ sản xuất phát sinh gần đây`
27. `Chi tiết phiếu nhập kho nội bộ số 001-2610-011362`
28. `Bảng kê nhập kho từ sản xuất của mã hàng RC4-3049-000`
29. `Mã hàng QC7-5146-000 được nhập kho khi nào trong tháng 10/2026? Từ kho nào sang và ai lập phiếu?`
30. `Tra cứu lần nhập kho gần đây nhất của mã vật tư RC4-3049-000`

### 4. Tra cứu MES Sản xuất, Đóng gói & Khuôn
31. `Bảng kê đóng gói đóng thùng thành phẩm gần đây nhất`
32. `Cho tôi xem bảng kê gộp tách thùng tem carton gần đây`
33. `Bảng kê bổ sung hoặc bỏ shot khuôn trong ca sản xuất gần đây`
34. `Tra cứu hồ sơ khuôn của mã khuôn K_VGY1A061`
35. `Danh sách các hồ sơ khuôn và tuổi thọ shot định mức mới cập nhật gần đây`
36. `Bảng kê điều độ sản xuất và danh sách Work Order đang chạy`
37. `Lịch sử các lần dừng máy stop line gần đây nhất`
38. `Bảng kê xác nhận phế phẩm NG sản xuất gần đây nhất`

### 5. Tra cứu Bảng giá & Định mức kỹ thuật (BOM)
39. `Danh mục bảng giá bán sản phẩm đang có hiệu lực hiện hành`
40. `Mã hàng QC7-5146-000 dùng loại hạt nhựa gì theo định mức BOM?`
41. `MOQ báo giá và đơn giá bán hiện hành áp dụng cho mã hàng QC7-5146-000 là bao nhiêu?`
42. `Mã hàng QC7-5146-000 thuộc quyền quản lý của khách hàng nào?`

---

## PHẦN 3: BỘ CÂU HỎI ĐỐI SOÁT PHỨC TẠP & SO SÁNH KỲ (ADVANCED PERIOD COMPARISON)
*Các câu hỏi đối soát nghiệp vụ chuyên sâu, so sánh 2 khoảng thời gian hoặc gom nhóm nhiều tiêu chí.*

43. **So sánh sản lượng xuất bán giữa 2 kỳ:**
    ```text
    So sánh số lượng xuất bán của mã hàng QC7-5146-000 từ ngày 01/10/2026 đến ngày 10/10/2026 so với từ ngày 11/10/2026 đến ngày 20/10/2026
    ```
    *(Kỳ vọng: AI tự động phân tích 2 kỳ, tính tổng số lượng từng kỳ và chênh lệch tăng/giảm)*

44. **So sánh doanh thu xuất bán giữa 2 đợt của khách hàng:**
    ```text
    Đối chiếu doanh thu và số lượng xuất bán của khách hàng KH0015 từ ngày 01/10/2026 đến ngày 10/10/2026 và từ ngày 11/10/2026 đến ngày 20/10/2026
    ```

45. **Đối soát cân đối giữa Đơn đặt hàng (SO) và Thực tế xuất giao (HDA):**
    ```text
    Kiểm tra tổng số lượng đặt hàng trong đơn SO và tổng số lượng đã xuất kho giao hàng của mã QC7-5146-000 trong tháng 10/2026
    ```

---

## BẢNG TRA CỨU NHANH CÁC THÔNG SỐ TEST THỰC TẾ (CHEAT SHEET)

Khi cần thay đổi tham số để test ngẫu nhiên, bạn có thể chọn các mã có sẵn dữ liệu thật trong cơ sở dữ liệu:

| Loại thông số | Các mã thực tế có sẵn dữ liệu | Ghi chú nghiệp vụ |
|---|---|---|
| **Mã vật tư / TP (`ma_vt`)** | `QC7-5146-000`, `RC4-3049-000`, `VGL1A416`, `PS-576D`, `PA66-101F` | Linh kiện nhựa máy in, hạt nhựa nguyên sinh |
| **Mã khách hàng (`ma_kh`)** | `KH0015`, `KH0047`, `KH0049`, `KH0001` | Canon Thăng Long, Anam Electronics, Tohoku Pioneer |
| **Mã nhà cung cấp (`ma_ncc`)**| `NCC0220`, `NCC0012`, `NCC0085` | Công ty Hungtech, Nhà cung cấp hạt nhựa |
| **Mã kho hàng (`ma_kho`)** | `KHOTP00`, `KHOTP02`, `KHO_TAIMAY`, `KHONVL`, `KHOPL` | Kho thành phẩm, Kho tại máy, Kho nguyên vật liệu |
| **Số đơn hàng bán (`so_ct`)** | `001-2610-010164`, `001-2610-010165` | Chứng từ SO1 tháng 10/2026 |
| **Số phiếu xuất kho (`so_ct`)**| `001-2610-002643`, `001-2610-001811` | Chứng từ xuất kho bán hàng HDA |
| **Số đơn mua hàng (`so_po`)** | `001-2610-000702`, `001-2610-000698` | Chứng từ đơn hàng mua PO1 |
| **Mã khuôn (`ma_khuon`)** | `K_VGY1A061`, `K_QC5-2919-000-V1` | Khuôn ép linh kiện cơ khí chính xác |
