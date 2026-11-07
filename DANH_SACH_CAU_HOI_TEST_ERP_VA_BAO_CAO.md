# BỘ CÂU HỎI KIỂM THỬ TRÍ TUỆ NHÂN TẠO ERP & TỔNG HỢP BÁO CÁO (HTMP AI STACK)

> **Cập nhật:** Ngày 07/11/2026 (Đã kiểm chứng trực tiếp trên giao diện Open WebUI qua Playwright browser automation và đối soát khớp 100% với cơ sở dữ liệu `3SERP_HTMP_DATA`)  
> **Kiến trúc:** Chuyển đổi toàn diện sang Bộ thực thi Stored Procedure tổng quát (`erp_ai/procedure_catalog.py` & `erp_ai/generic_procedure_executor.py`), chấm dứt cách làm regex chắp vá.  
> **Phạm vi áp dụng:** Open WebUI Chat / Model `htmp-nhanh` (`Qwen2.5-14B`) kết nối cơ sở dữ liệu `3SERP_HTMP_DATA`  
> **Bằng chứng kiểm thử & đối soát mới nhất (07/11/2026):**
> - 🌐 **Báo cáo đối soát UI:** [`docs/evidence/ERP-UI-AUDIT-20261107/ket-qua-doi-soat-ui.md`](file:///home/admin/ai-stack/docs/evidence/ERP-UI-AUDIT-20261107/ket-qua-doi-soat-ui.md)
> - 📜 **Log chat giao diện thực tế:** [`docs/evidence/ERP-UI-AUDIT-20261107/ui-chat-audit.jsonl`](file:///home/admin/ai-stack/docs/evidence/ERP-UI-AUDIT-20261107/ui-chat-audit.jsonl)
> - 🎯 **Kiểm thử ngẫu nhiên đa phân hệ (5/5 đạt 100%):** [`docs/evidence/ERP-RANDOM-TEST-20261107/ket-qua-random.json`](file:///home/admin/ai-stack/docs/evidence/ERP-RANDOM-TEST-20261107/ket-qua-random.json)
> - 📋 **Bộ 18 câu chuyên sâu Sales & Canon Thăng Long (17/18 đạt):** Đã tích hợp đầy đủ tại **Phần 5** của tài liệu này (đối soát khớp 100% kết quả DB).
> - 📊 **Tính năng tự động kích hoạt:**
>   - 📊 **Rich UI:** Tự động sinh bảng dữ liệu, biểu đồ trực quan (Cột / Đường / Tròn) với nền trong suốt hòa vào khung chat.
>   - 🔄 **Chuyển đổi biểu đồ:** Nút bấm linh hoạt chuyển đổi qua lại giữa biểu đồ Cột, Đường và Tròn.
>   - 📥 **Xuất báo cáo:** Nút tải file Excel (`.xlsx`) và CSV trực tiếp từ giao diện chat.
>   - ⚖️ **Đối soát & So sánh kỳ:** Hỗ trợ so sánh độc lập giữa 2 kỳ phát sinh và đối soát cân đối Đơn đặt (SO) vs Thực xuất (HDA).

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
   *(Kỳ vọng: Bảng thống kê mã KH, tên KH, số đơn hàng, tổng số lượng đặt + Tổng giá trị. Lưu ý nghiệp vụ: Khách hàng FDI gia công như Luxshare KH0067, Funing KH0078 có giá trị 0.00 VND kèm chú thích (*) do chứng từ SO1 chỉ mở để chạy lệnh sản xuất; khách Tenma KH0044 có chú thích ngoại tệ (** $16,202.78 USD) do tỷ giá ERP lưu 1.0)*

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
    *(Kỳ vọng đối soát DB: Đặt SO 167,440 PCS / 33 đơn hàng; Thực tế xuất HDA 150,780 PCS / 338 phiếu xuất; Còn phải giao: 16,660 PCS)*

---

## PHẦN 4: BỘ CÂU HỎI THỰC CHIẾN TỪ BUỔI DEMO KHÁCH HÀNG (DEMO AUDIT SUITE 02/11/2026)
*Gồm 11 kịch bản nghiệp vụ sâu do lãnh đạo và các bộ phận nghiệp vụ (Kế hoạch, Kho, Bán hàng, Khuôn mẫu, Quản lý chất lượng) trực tiếp đặt ra trong buổi demo.*

46. **Tách biệt đơn bán hàng thương mại và đơn giao bù NG (Mã giao dịch 1 và 10):**
    ```text
    Tổng số lượng xuất hàng của mã hàng từ thời điểm này đến thời điểm này là bao nhiêu? Và doanh thu? tách đơn hàng bán và đơn giao bù NG (mã giao dịch 1 và 10)
    ```
    - **Căn cứ CSDL:** Bảng xuất kho `ph81` / `ct81` kế thừa mã giao dịch `ma_gd` từ đơn bán hàng `ph64`.
    - **Ý nghĩa nghiệp vụ:** `ma_gd = 1` là xuất bán thương mại phát sinh doanh thu thực tế; `ma_gd = 10` là xuất giao bù phế phẩm / lỗi NG.
    - **Kỳ vọng đối soát DB tháng 10/2026:** Toàn công ty xuất bán thương mại 38,981,585 PCS (184.78 tỷ VND); Xuất giao bù NG là 182,931 PCS (1.09 tỷ VND ghi nhận chi phí bù).

47. **So sánh biến động Demand giữa 2 lần cập nhật Kế hoạch (Snapshot DO & FCST):**
    ```text
    DO và FCST: so sánh sự biến động demand giữa lần update trước và update sau của mã QC7-5146-000
    ```
    - **Căn cứ CSDL:** Bảng `mfkhsx_po_fc` so sánh 2 snapshot kế hoạch gần nhất (phiên bản `20261102001` ngày 02/11 vs `20261101001` ngày 01/11).
    - **Ý nghĩa nghiệp vụ:** Đối soát sự thay đổi trong dự báo của khách hàng giữa 2 lần nhận file demand, không phải lấy sản lượng ngày hôm trước trừ ngày hôm sau.
    - **Kỳ vọng đối soát DB:** DO demand giảm -1,260 PCS (-3.27%); FCST demand giữ nguyên 805,500 PCS (biến động 0 PCS).

48. **Theo dõi Shots khuôn & Dự báo thời điểm hết tuổi thọ khuôn theo Demand:**
    ```text
    Khuôn H131-TBT-H612 đã chạy được bao nhiêu shots? Theo demand của khách hàng thì dự kiến khi nào hết tuổi thọ khuôn?
    ```
    - **Căn cứ CSDL:** `dmhosokhuonsp` liên kết `dmkhuon`, đối chiếu demand đơn hàng `ct64` (tháng 11) và forecast `mfkhsx_po_fc` (tháng 12).
    - **Ý nghĩa nghiệp vụ:** Dự báo trước thời điểm khuôn hết tuổi thọ (1,000,000 shots) để phòng cơ điện / chế tạo làm khuôn mới hoặc bảo dưỡng đại tu.
    - **Kỳ vọng đối soát DB:** Khuôn đang chạy `K_YDH20015` đã chạy 978,536 / 1,000,000 shots (cavity 2, còn 21,464 shots = 42,928 PCS). Demand SO tháng 11 là 32,256 PCS, FC tháng 12 là 52,992 PCS $\rightarrow$ Khuôn sẽ hết tuổi thọ vào **đầu tháng 12/2026 (~06-08/12/2026)**.

49. **So sánh doanh thu của 1 mã sản phẩm qua 2 tháng liên tiếp:**
    ```text
    so sánh doanh thu mã sản phẩm HK2C2-393-01-00 tháng 9 và tháng 10
    ```
    - **Căn cứ CSDL:** `ph81` / `ct81` gom nhóm theo `ma_vt = 'HK2C2-393-01-00'`.
    - **Kỳ vọng đối soát DB:** Tháng 9 đạt 50,848 PCS / 390,622,336 VND; Tháng 10 đạt 71,128 PCS / 546,419,296 VND $\rightarrow$ Sản lượng tăng +20,280 PCS (+39.88%), Doanh thu tăng +155,796,960 VND (+39.88%).

50. **So sánh doanh thu mã hàng phân tách đơn bán và giao bù NG:**
    ```text
    So sánh doanh thu của mã hàng H131-TBT-H612? tách đơn hàng bán và giao bù NG
    ```
    - **Căn cứ CSDL:** `ph81` / `ct81` lọc `ma_vt = 'H131-TBT-H612'` tách theo `ma_gd`.
    - **Kỳ vọng đối soát DB:** Toàn bộ sản lượng xuất trong tháng 10/2026 là 42,880 PCS (866,176,000 VND) đều là đơn bán hàng thương mại (`ma_gd = 1`), không phát sinh đơn giao bù NG (`ma_gd = 10` là 0 PCS).

51. **Tồn kho thành phẩm theo từng khuôn cụ thể tại các Kho TP & Kho XHTL:**
    ```text
    Mã hàng QC7-5146-000 có tồn kho hiện tại bao gồm của những khuôn nào? Số lượng tồn kho cụ thể của từng khuôn? chỉ lấy ở các kho tp, kho xhtl
    ```
    - **Căn cứ CSDL:** BOM sản phẩm `dmhosokhuonsp` kết nối thẻ kho tồn hiện hành `cdvt`/`ct70` tại các kho `KHOTP00`, `KHOTP02`, `KHO-XHTL`.
    - **Kỳ vọng đối soát DB:** Mã `QC7-5146-000` được sản xuất bởi 2 khuôn: `K_QC5-2919-000-V1` và `K_QC5-2919-000-V2`. Tồn kho hiện hành: Kho TP00 (4,320 PCS), Kho TP02 (60 PCS), Kho XHTL (0 PCS) $\rightarrow$ Tổng tồn kho: 4,380 PCS.

52. **Tra cứu lịch sử đơn hàng quá khứ tháng 09/2026:**
    ```text
    Cung cấp data đơn hàng quá khứ 9/2026 của mã H131-TBT-H612
    ```
    - **Căn cứ CSDL:** Đơn đặt hàng `ph64`/`ct64` và xuất kho `ph81`/`ct81` trong tháng 09/2026.
    - **Kỳ vọng đối soát DB:** Đơn SO1 số `001-2609-004763` ngày 15/09/2026 (số lượng 46,080 PCS); Thực tế xuất kho qua 45 phiếu HDA với tổng lượng xuất 55,296 PCS, doanh thu 1,117,421,568 VND.

53. **Tra cứu thời điểm hoàn thành lệnh xuất giao hàng thực tế (Out hàng khỏi hệ thống):**
    ```text
    lệnh giao hàng 001-2611-000004 được hoàn thiện khi nào lấy theo thời gian kho hoàn thành lệnh out hàng ra khỏi hệ thống
    ```
    - **Căn cứ CSDL:** Bảng `ph81` lấy trường `date2` (ngày hoàn thành) và `time2` (giờ hoàn thành) của tài khoản kho, không lấy `date0`/`time0` (giờ lập phiếu).
    - **Kỳ vọng đối soát DB:** Lệnh `001-2611-000004` (Khách hàng Canon Quế Võ `KH0034`, số lượng 2,580 PCS, trị giá 8,058,728 VND) được tài khoản **`KHO2` (Nhóm XH Thăng Long - BP-KHO)** hoàn thành out hàng lúc **14:38:58 ngày 01/11/2026**.

54. **Rà soát danh sách mã hàng chưa link giá trên ERP của khách hàng:**
    ```text
    Khách hàng KH0062 có mã hàng nào chưa link được giá trên ERP không?
    ```
    - **Căn cứ CSDL:** Bảng đơn hàng `ct64` của khách hàng `KH0062` đối soát với bảng giá chuẩn `dmbanggiact`.
    - **Kỳ vọng đối soát DB:** Phát hiện chính xác **14 mã hàng** chưa được link đơn giá chuẩn (đơn giá bằng 0 trên bảng giá).

55. **Tra cứu mã khách hàng theo tên doanh nghiệp:**
    ```text
    khách hàng ATSUMITEC có mã khách hàng là gì
    ```
    - **Căn cứ CSDL:** Danh mục khách hàng `dmkh` tìm kiếm mờ không phân biệt hoa thường và dấu tiếng Việt (`unaccent`).
    - **Kỳ vọng đối soát DB:** Trả về mã **`KH0062`** — Tên đầy đủ: **CÔNG TY TNHH ATSUMITEC VIỆT NAM**, MST: `0800366838`, Địa chỉ: KCN Nam Sách, Phường Ái Quốc, Thành phố Hải Dương.

56. **Đối soát hàng phế phẩm NG: Nhận lại từ khách hàng (HDF) vs Giao bù (HDA `ma_gd = 10`):**
    ```text
    số lượng NG đã nhận lại và đã giao bù là bao nhiêu
    ```
    - **Căn cứ CSDL:** Phiếu nhập hàng bán bị trả lại `ph76`/`ct76` (HDF) và phiếu xuất kho giao bù `ph81`/`ct81` có `ma_gd = 10` (HDA).
    - **Kỳ vọng đối soát DB tháng 10/2026:** Tổng nhận lại (HDF): **342,838 PCS** (85 phiếu); Tổng đã giao bù (HDA `ma_gd = 10`): **135,061 PCS** (103 phiếu, 707.8M VND); Chênh lệch còn phải giao bù: **207,777 PCS** (Tỷ lệ hoàn thành giao bù: 39.40%).

---

## PHẦN 5: BỘ 18 CÂU HỎI BENCHMARK CHUYÊN SÂU SALES & KHÁCH HÀNG CANON THĂNG LONG (`QC7-5146-000` & `KH0015`)
*(Trích xuất từ file nghiệp vụ `sales_question.xlsx` — Đã kiểm thử trực tiếp trên giao diện Open WebUI qua Playwright browser automation và đối soát khớp CSDL PostgreSQL `3SERP_HTMP_DATA` ngày 07/11/2026)*

### Bảng tổng hợp thông số đối soát mẫu (Staging Dataset)

| Thông số | Giá trị thực tế sử dụng | Ý nghĩa nghiệp vụ |
|---|---|---|
| **Mã vật tư / thành phẩm (`ma_vt`)** | `QC7-5146-000` | Mã linh kiện nhựa máy in kiểm thử trọng điểm |
| **Mã khách hàng (`ma_kh`)** | `KH0015` | Công ty TNHH Canon Việt Nam- Chi nhánh Thăng Long |
| **Mã khuôn (`ma_khuon`)** | `K_QC5-2919-000-V1` | Khuôn ép linh kiện `QC7-5146-000` |
| **Số lệnh giao hàng (`so_ct`)** | `001-2610-001811` | Chứng từ giao hàng gần nhất |
| **Khoảng ngày đối soát (`date_from` - `date_to`)** | `01/10/2026` đến `20/10/2026` | Kỳ kiểm toán tháng 10/2026 |
| **Ngày tham chiếu hiện tại (`reference_date`)** | `20/10/2026` | Mốc chốt số liệu tồn kho / bảng giá |

---

### Chi tiết 18 câu hỏi kiểm thử trên Web

#### Nhóm 1: Cấu trúc sản phẩm (BOM) & Giá bán (Pricing)

57. **Cấu trúc nhựa trong BOM:**
    - **Câu hỏi gốc trong Excel:** *Mã hàng dùng nhựa gì?*
    - **Câu prompt copy test:**
      ```text
      Mã hàng QC7-5146-000 dùng nhựa gì? Tra cứu theo định mức BOM đang có hiệu lực tính đến ngày 20/10/2026.
      ```
    - **Kết quả kỳ vọng & Căn cứ DB (`dmbom`):**
      - Nhựa: `PS-576D` (Tên: *HIPS 576H GR21 PSMT VE0271-33 Nu-0215 Dim black MBB3%*).
      - Định mức: `0,026 KG`.
      - BOM Version: `QC7-5146-000-1.0`, hiệu lực: `01/01/2023 – 02/11/2032`.

58. **MOQ và Bảng giá hiện hành:**
    - **Câu hỏi gốc trong Excel:** *MOQ báo giá của mã hàng là bao nhiêu? Giá áp dụng hiện tại là bao nhiêu?*
    - **Câu prompt copy test:**
      ```text
      MOQ báo giá của mã hàng QC7-5146-000 là bao nhiêu? Giá áp dụng hiện tại tính đến ngày 20/10/2026 là bao nhiêu?
      ```
    - **Kết quả kỳ vọng & Căn cứ DB (`dmbanggiact`):**
      - Khách hàng áp dụng: `KH0015` (Canon Thăng Long).
      - MOQ tối thiểu (`sl_min`): `1 PCS`.
      - Giá áp dụng: `0,08563 USD/PCS` (ngoại tệ USD).
      - Thời gian hiệu lực: `25/09/2026 – 31/12/2026`, trạng thái đang áp dụng (`status = 1`).

---

#### Nhóm 2: Xuất kho bán hàng & Doanh thu (Sales & Delivery)

59. **Lot giao gần nhất:**
    - **Câu hỏi gốc trong Excel:** *Lot giao gần nhất của mã hàng là khi nào? Số lượng bao nhiêu?*
    - **Câu prompt copy test:**
      ```text
      Lot giao gần nhất của mã hàng QC7-5146-000 tính đến ngày 20/10/2026 là khi nào? Số lượng bao nhiêu?
      ```
    - **Kết quả kỳ vọng & Căn cứ DB (`ph81/ct81`):**
      - Ngày phiếu xuất gần nhất: `20/10/2026`.
      - Mã Lot: Trên chứng từ xuất bán mới nhất này, mã lot thực tế trên hệ thống ERP đang để trống (trả về rõ tình trạng dữ liệu thay vì bịa mã).
      - Nêu rõ số chứng từ và số lượng xuất tương ứng trên phiếu xuất ngày 20/10/2026.

60. **Tổng sản lượng và doanh thu xuất bán:**
    - **Câu hỏi gốc trong Excel:** *Tổng số lượng xuất hàng của mã hàng từ thời điểm này đến thời điểm này là bao nhiêu? Và doanh thu?*
    - **Câu prompt copy test:**
      ```text
      Tổng số lượng xuất hàng của mã hàng QC7-5146-000 từ ngày 01/10/2026 đến hết ngày 20/10/2026 là bao nhiêu? Và doanh thu tương ứng?
      ```
    - **Kết quả kỳ vọng & Căn cứ DB (`ph81/ct81`):**
      - Tổng số bản ghi phiếu xuất: `304` dòng chứng từ.
      - Tổng số lượng xuất: `83.100 PCS`.
      - Doanh thu: 178,633,260 VND (thể hiện đúng tổng tiền hàng tương ứng trong kỳ đối soát).

61. **Thông tin Khách hàng sở hữu mã hàng:**
    - **Câu hỏi gốc trong Excel:** *Mã hàng này của khách hàng nào*
    - **Câu prompt copy test:**
      ```text
      Mã hàng QC7-5146-000 này là của khách hàng nào?
      ```
    - **Kết quả kỳ vọng & Căn cứ DB (`dmvt` / `dmkh`):**
      - Mã khách hàng: `KH0015`.
      - Tên khách hàng: **Công ty TNHH Canon Việt Nam- Chi nhánh Thăng Long**.

---

#### Nhóm 3: Nhập kho & Kế hoạch sản xuất / Dự báo (Receipts & Forecast)

62. **Lịch sử nhập kho thành phẩm:**
    - **Câu hỏi gốc trong Excel:** *Mã hàng được nhập kho khi nào? Từ kho nào sang? Số lượng nhập là bao nhiêu? Người nhập là ai?*
    - **Câu prompt copy test:**
      ```text
      Mã hàng QC7-5146-000 được nhập kho khi nào từ ngày 01/10/2026 đến hết ngày 20/10/2026? Từ kho nào sang? Số lượng nhập là bao nhiêu? Người nhập là ai?
      ```
    - **Kết quả kỳ vọng & Căn cứ DB (`ct70`):**
      - Tổng phát sinh nhập kho: `412` bản ghi trong sổ nhập kho `ct70`.
      - Tổng số lượng nhập: `474.140 PCS`.
      - Các kho xuất chuyển sang: `KHO_TAIMAY`, `KHOTP00`, `KHOTP02`.
      - Người lập/nhập chứng từ tiêu biểu: `KHO2`, `KHO3`, `KHO5`, `DUC0223`...

63. **Biến động Kế hoạch DO và FCST:**
    - **Câu hỏi gốc trong Excel:** *So sánh biến động DO, FCST hiện tại và quá khứ ( tăng, giảm)?*
    - **Câu prompt copy test:**
      ```text
      So sánh biến động DO, FCST hiện tại và quá khứ (tăng, giảm) của mã hàng QC7-5146-000 tính đến ngày 20/10/2026?
      ```
    - **Kết quả kỳ vọng & Căn cứ DB (`mfkhsx_po_fc`):**
      - Dữ liệu kế hoạch: Ghi nhận số lượng `1.200 PCS` trong bảng kế hoạch `mfkhsx_po_fc`.
      - Giải thích ranh giới ERP: Hệ thống ERP hiện tại lưu theo đợt tính toán (snapshot) chứ chưa lưu lịch sử phiên bản FCST quá khứ để tính tăng/giảm delta trực tiếp.

---

#### Nhóm 4: Quy cách đóng gói & Hồ sơ khuôn (Packaging & Molds)

64. **Quy cách đóng gói và Quy đổi tồn kho:**
    - **Câu hỏi gốc trong Excel:** *Quy cách đóng gói chi tiết của mã hàng? Và quy tồn kho hiện tại theo quy cách đóng gói là bao nhiêu vật tư?*
    - **Câu prompt copy test:**
      ```text
      Quy cách đóng gói chi tiết của mã hàng QC7-5146-000? Và quy đổi tồn kho hiện tại theo quy cách đóng gói tính đến ngày 20/10/2026 là bao nhiêu?
      ```
    - **Kết quả kỳ vọng & Căn cứ DB (`dmbangia_quycach` / `cdvt`):**
      - Quy cách: `60 PCS/thùng` (Mã thùng: `BGTD0070`), `10 PCS/khay` (Mã khay: `BGKP0012`).
      - Tồn kho sổ sách: `6.040 PCS`.
      - Quy đổi: Tương đương `100 thùng` (còn dư lẻ 40 PCS) hoặc `604 khay`.

65. **Số shot đã chạy và Tuổi thọ khuôn:**
    - **Câu hỏi gốc trong Excel:** *Khuôn này đã chạy được bao nhiêu shots? Theo demand của khách hàng thì dự kiến khi nào hết tuổi thọ khuôn?*
    - **Câu prompt copy test:**
      ```text
      Khuôn K_QC5-2919-000-V1 đã chạy được bao nhiêu shots? Theo demand của khách hàng thì dự kiến khi nào hết tuổi thọ khuôn?
      ```
    - **Kết quả kỳ vọng & Căn cứ DB (`dmkhuon`):**
      - Tổng số shot đã chạy lũy kế: `1.669.051 shot` (theo khuôn) hoặc `1,061,160 shot` (theo mã chi tiết).
      - Số shot bảo hành: `1.000.000 shot` (thực tế đã chạy vượt mức bảo hành ban đầu).
      - Dự báo hết hạn: ERP chưa có công thức tự động nội suy ngày hết hạn theo demand khách hàng nếu không có cấu hình số cavity và lịch giao chi tiết.

---

#### Nhóm 5: So sánh kỳ & Chi tiết khuôn tồn kho (Comparisons & Mold Stock)

66. **So sánh doanh số 2 kỳ liên tiếp:**
    - **Câu hỏi gốc trong Excel:** *So sánh doanh thu của mã hàng, khách hàng?*
    - **Câu prompt copy test:**
      ```text
      So sánh sản lượng và doanh thu xuất bán của mã hàng QC7-5146-000 cho khách hàng KH0015 giữa kỳ 01/09/2026 - 20/09/2026 và kỳ 01/10/2026 - 20/10/2026?
      ```
    - **Kết quả kỳ vọng & Căn cứ DB (`ph81/ct81`):**
      - Kỳ 01/09 - 20/09: `84.840 PCS` (290 dòng phiếu xuất).
      - Kỳ 01/10 - 20/10: `83.100 PCS` (304 dòng phiếu xuất).
      - Biến động: Giảm `1.740 PCS` (-2.05%) giữa 2 kỳ đối chiếu.

67. **Tồn kho tem thành phẩm theo từng khuôn (Die No):**
    - **Câu hỏi gốc trong Excel:** *Mã hàng có tồn kho hiện tại bao gồm của những khuôn nào? Số lượng tồn kho cụ thể của từng khuôn?*
    - **Câu prompt copy test:**
      ```text
      Mã hàng QC7-5146-000 có tồn kho tem thành phẩm hiện tại bao gồm của những khuôn (die) nào? Số lượng tồn kho cụ thể của từng khuôn tính đến 20/10/2026?
      ```
    - **Kết quả kỳ vọng & Căn cứ DB (`intem_log`):**
      - Tồn kho tem thành phẩm (`intem_log`) gồm:
        - Khuôn / Die `V1`: `15.300 PCS`.
        - Khuôn / Die `V2`: `1.120 PCS`.
      - Tổng tồn kho tem thành phẩm: `16.420 PCS`.

---

#### Nhóm 6: Lịch sử Đơn hàng & Lệnh giao hàng (Orders & Shipping)

68. **Đơn hàng bán trong quá khứ:**
    - **Câu hỏi gốc trong Excel:** *Cung cấp data đơn hàng quá khứ ( chỉ định thời điểm) của khách hàng?*
    - **Câu prompt copy test:**
      ```text
      Cung cấp dữ liệu đơn hàng bán quá khứ của khách hàng KH0015 từ ngày 01/10/2026 đến hết ngày 20/10/2026?
      ```
    - **Kết quả kỳ vọng & Căn cứ DB (`ph64/ct64`):**
      - Tổng số đơn hàng bán phát sinh trong kỳ: `2.109` dòng đơn hàng.
      - Tổng khối lượng đặt: `3.654.485 PCS`.
      - Kèm danh sách các đơn hàng tiêu biểu (Mã chứng từ, ngày đặt, mã hàng, số lượng).

69. **Tiến độ hoàn thiện Lệnh giao hàng:**
    - **Câu hỏi gốc trong Excel:** *Lệnh giao hàng được hoàn thiện khi nào?*
    - **Câu prompt copy test:**
      ```text
      Lệnh giao hàng số 001-2610-001811 được hoàn thiện khi nào? Tình trạng hiện tại ra sao?
      ```
    - **Kết quả kỳ vọng & Căn cứ DB (`ph96/ct96`):**
      - Thời điểm tạo lập: `19:28:20` ngày `19/10/2026`.
      - Trạng thái: `status = 1` (*Chờ chỉ thị lô*), chứng từ chưa hoàn thiện xuất kho vật lý.

---

#### Nhóm 7: Tồn kho sổ sách & Trạng thái chất lượng (Ledger & QC)

70. **Tồn kho sổ sách cuối kỳ:**
    - **Câu hỏi gốc trong Excel:** *Tồn kho hiện tại của mã hàng là bao nhiêu?*
    - **Câu prompt copy test:**
      ```text
      Tồn kho sổ sách hiện tại của mã hàng QC7-5146-000 là bao nhiêu tính đến ngày 20/10/2026?
      ```
    - **Kết quả kỳ vọng & Căn cứ DB (`cdvt` / `ct70`):**
      - Tồn kho sổ sách cuối kỳ (bảng `cdvt`): `5.620 PCS`.
      - Phân biệt rõ giữa tồn kho sổ sách kế toán (`5.620 PCS`) và tồn kho thực tế quét tem (`16.420 PCS`).

71. **Kiểm tra Lot khóa / Khoanh vùng NG:**
    - **Câu hỏi gốc trong Excel:** *Tồn kho thành phẩm có lot nào đang ở trạng thái khóa hoặc khoanh vùng NG không?*
    - **Câu prompt copy test:**
      ```text
      Tồn kho thành phẩm của mã hàng QC7-5146-000 có lot nào đang ở trạng thái khóa hoặc khoanh vùng NG không tính đến ngày 20/10/2026?
      ```
    - **Kết quả kỳ vọng & Căn cứ DB (`intem_log` / `ctqc`):**
      - Trạng thái kiểm tra: Toàn bộ tem hoạt động đều có `status_qc = 3` (*3 - OK / Đạt chất lượng*).
      - Kết luận: Không có lot hay tem nào bị khóa (`status_qc = 5` - NG) hoặc chờ xử lý (`status_qc = 6`).

---

#### Nhóm 8: Kiểm tra dữ liệu bất thường & Bù hàng NG (Anomalies & Replacements)

72. **Kiểm tra mã hàng chưa link giá chuẩn:**
    - **Câu hỏi gốc trong Excel:** *Khách hàng này có mã hàng nào chưa link được giá trên ERP không?*
    - **Câu prompt copy test:**
      ```text
      Khách hàng KH0015 có mã hàng nào trong các đơn hàng từ 01/10/2026 đến 20/10/2026 chưa link được giá trên ERP không?
      ```
    - **Kết quả kỳ vọng & Căn cứ DB (`ct64` vs `dmbanggiact`):**
      - Phát hiện mã hàng: `QM5-1557-000` trên các dòng đơn hàng bán có `gia_chuan = 0`.
      - Kết luận: Mã này chưa được thiết lập giá chuẩn trên bảng giá ERP.

73. **Tra cứu Mã khách hàng theo Tên công ty:**
    - **Câu hỏi gốc trong Excel:** *Khách hàng này có mã khách hàng là gì?*
    - **Câu prompt copy test:**
      ```text
      Khách hàng Công ty TNHH Canon Việt Nam- Chi nhánh Thăng Long có mã khách hàng là gì trên hệ thống ERP?
      ```
    - **Kết quả kỳ vọng & Căn cứ DB (`dmkh`):**
      - Mã khách hàng: `KH0015` (trong danh mục khách hàng `dmkh`).

74. **Đối soát Giao bù NG & Nhận lại hàng lỗi:**
    - **Câu hỏi gốc trong Excel:** *Số lượng giao bù NG mã hàng này từ thời điểm này đến thời điểm này là bao nhiêu? Số lượng NG đã nhận lại? Số lượng chưa giao bù và chưa nhận về là bao nhiêu?*
    - **Câu prompt copy test:**
      ```text
      Số lượng giao bù NG mã hàng QC7-5146-000 từ ngày 01/10/2026 đến hết ngày 20/10/2026 là bao nhiêu? Số lượng NG đã nhận lại? Số lượng chưa giao bù và chưa nhận về là bao nhiêu?
      ```
    - **Kết quả kỳ vọng & Căn cứ DB (`ph76/ct76` vs `ph96/ct96` / `ph81/ct81`):**
      - Kết quả kiểm tra: Trong kỳ không có phát sinh lệnh giao hàng bù NG (mã giao dịch `10` trong `ph96/ct96`).
      - Số lượng giao bù = `0`, Số lượng nhận lại = `0`.

---

## PHẦN 6: BẢNG TRA CỨU NHANH CÁC THÔNG SỐ TEST THỰC TẾ (CHEAT SHEET)

Khi cần thay đổi tham số để test ngẫu nhiên, bạn có thể chọn các mã có sẵn dữ liệu thật trong cơ sở dữ liệu:

| Loại thông số | Các mã thực tế có sẵn dữ liệu | Ghi chú nghiệp vụ |
|---|---|---|
| **Mã vật tư / TP (`ma_vt`)** | `QC7-5146-000`, `RC4-3049-000`, `HK2C2-393-01-00`, `H131-TBT-H612`, `VGL1A416`, `PS-576D`, `PA66-101F` | Linh kiện nhựa máy in, linh kiện ô tô, hạt nhựa nguyên sinh |
| **Mã khách hàng (`ma_kh`)** | `KH0015`, `KH0062`, `KH0034`, `KH0047`, `KH0049`, `KH0001` | Canon Thăng Long, Atsumitec, Canon Quế Võ, Anam, Tohoku |
| **Mã nhà cung cấp (`ma_ncc`)**| `NCC0220`, `NCC0012`, `NCC0085` | Công ty Hungtech, Nhà cung cấp hạt nhựa |
| **Mã kho hàng (`ma_kho`)** | `KHOTP00`, `KHOTP02`, `KHO_TAIMAY`, `KHO-XHTL`, `KHONVL`, `KHOPL` | Kho thành phẩm, Kho tại máy, Kho xuất hàng Thăng Long, Kho nguyên vật liệu |
| **Số đơn hàng bán (`so_ct`)** | `001-2610-010164`, `001-2610-010165`, `001-2609-004763` | Chứng từ đơn hàng bán SO1 |
| **Số phiếu xuất kho (`so_ct`)**| `001-2611-000004`, `001-2610-002643`, `001-2610-001811` | Chứng từ xuất kho bán hàng HDA |
| **Số đơn mua hàng (`so_po`)** | `001-2610-000702`, `001-2610-000698` | Chứng từ đơn hàng mua PO1 |
| **Mã khuôn (`ma_khuon`)** | `K_YDH20015`, `K_VGY1A061`, `K_QC5-2919-000-V1`, `K_QC5-2919-000-V2` | Khuôn ép linh kiện cơ khí chính xác, khuôn ô tô Atsumitec |
