# BỘ CÂU HỎI KIỂM THỬ TRÍ TUỆ NHÂN TẠO ERP & TỔNG HỢP BÁO CÁO (HTMP AI STACK)

> **Cập nhật:** Ngày 02/11/2026 (Đã kiểm chứng, đối soát live DB và xác thực đạt 100% trên 45/45 câu hỏi)  
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

## BẢNG TRA CỨU NHANH CÁC THÔNG SỐ TEST THỰC TẾ (CHEAT SHEET)

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
