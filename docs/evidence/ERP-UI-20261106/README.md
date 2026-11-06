# Khảo sát giao diện và metadata ERP — 06/11/2026

## Phạm vi và mức bằng chứng

Khảo sát từ phiên Edge ERP do người dùng đăng nhập, qua SSH tunnel chỉ gắn loopback. Giao diện hiển thị tài khoản IT.ERP và đơn vị HTMP QM. Chỉ mở menu/màn hình; không lưu, duyệt, xóa, ghi sổ hoặc sửa dữ liệu. Các truy vấn catalog và phép đối chiếu dữ liệu chạy trong giao dịch PostgreSQL READ ONLY. Không ghi mật khẩu, cookie hoặc token vào tài liệu này.

Danh mục [screen-inventory.csv](screen-inventory.csv) tổng hợp 254 mã mục khác nhau trích từ menu của phiên UI. Một mã có thể là nhóm menu, màn hình hoặc mục chức năng, không mặc nhiên là 254 màn nghiệp vụ độc lập. Kết quả mở màn hình và nhãn lọc thô được lưu trong [survey.json](survey.json); một số đường dẫn khác tên state, hoặc nội dung tải chưa đủ. `opened_matching_url` là phép kiểm tra tên state trong URL, chỉ là dấu hiệu đã điều hướng, không chứng minh nội dung hay nghiệp vụ đúng.

Theo ghép tên state trong metadata DB tại thời điểm khảo sát, 113/254 mục có bản ghi `sys_reports`, 74 có cấu hình `sys_reportparams`, 64 có function `public` trùng tên. Đây là các phép ghép kỹ thuật; function trùng tên chưa chứng minh giao diện gọi function đó. Nhãn/cột metadata không xác minh join, công thức, quyền, phân trang hoặc số liệu hiển thị.

Lượt đầu thử 74 màn báo cáo, 73 đường dẫn khớp heuristic và 72 có văn bản điều kiện lọc. Lượt danh mục thử 64 màn, 21 URL khớp heuristic; cách lấy thẻ `<th>` không thu được nhãn cột và một số điều hướng không khớp. Đã thử thêm 46 màn chứng từ; 39 URL khớp heuristic, 7 chuyển sang URL tên khác (ví dụ các màn in tem). Lượt thử lại 43 màn danh mục có 42 URL khớp heuristic nhưng chỉ 12 màn có tiêu đề tải được trong thời gian chờ; không coi URL khớp là giao diện đã tải đầy đủ. Gộp các lượt, 175 mã menu có ít nhất một URL khớp heuristic; chưa xem chi tiết hay xác nhận đầy đủ nội dung. Phần còn lại cần mở và xác minh lại từng màn, không coi các lượt thử là hoàn thành toàn bộ ERP.

## Đối chiếu sâu: Báo cáo tồn theo kho

- **UI đã quan sát:** `InBCTonTheoKho`, tên “Báo cáo tồn theo kho”; có Đến ngày, Kho hàng, Mã vật tư, Nhóm VT 1–6, TK vật tư, Mã ĐVCS, Nhóm theo, Trạng thái kho và Mẫu báo cáo. Trường Đến ngày của phiên quan sát mặc định 2026-11-06. Hai tham số trạng thái kho và mẫu báo cáo được đánh dấu bắt buộc.
- **Metadata DB đã đọc:** `sys_reportparams` có cùng các tham số tương ứng `dto`, `cma_kho`, `cma_vt`, `cnh_vt1`–`cnh_vt6`, `ctk_vt`, `cma_dvcs`, `cgroup`, `cstatus`, `mau_bc`; `dto` có mặc định `CURRENT_DATE`. `sys_reports` có mẫu 001 và 002 với grid `InBCTonTheoKho1` và `InBCTonTheoKho2`.
- **Nguồn function đã đọc, chưa thực thi:** `public.inbctontheokho(params character varying)` tham chiếu `cdvt`, `ct70`, `dmvt`, `dmkho`, `sys_getrolerecord`. Mã có SQL động, bảng tạm và các thao tác insert/update bảng tạm; không gọi function này trong khảo sát. Điều kiện vật tư, kho/ĐVCS, nhóm vật tư và trạng thái kho được xây trong function.
- **Thời gian:** trong nhánh đọc `ct70`, source ghép `ngay_ct` và `to_char(time0, 'HH:MI:SS')` rồi lọc từ đầu kỳ đến `dto 06:00:00`. Đây là nội dung source quan sát được, không được tự đổi thành 23:59 hoặc diễn giải là thời điểm người dùng hỏi. Định dạng `HH` và ý nghĩa `time0`, thời điểm lưu hay giờ nghiệp vụ cần kiểm tra với người phụ trách ERP.
- **Kiểm tra ứng viên chỉ đọc:** với `75577-BZ010`, tồn đầu 2026 cộng phát sinh đến 05/11/2026 06:00 theo biểu thức thời gian nêu trên cho `KHO-LAP-RAP` 266 SET, `KHOTP00` 246 SET, `KHOTP03` -28 SET. Đây là truy vấn tham khảo chưa áp dụng đầy đủ toàn bộ điều kiện function và quyền UI; chưa chạy báo cáo thực tế để đối chiếu, không phải số đã nghiệm thu hay số tại 15:28.
- **Khoảng trống:** phải chạy báo cáo trên UI với đúng mã, ngày, kho, trạng thái, mẫu và cùng quyền; đối chiếu output API, nội dung lưới và phép tính độc lập. Đặc biệt xác nhận dòng âm, giờ chốt 06:00, cách function xử lý giờ 12/24 và phép phân quyền `sys_getrolerecord`.

## Quan sát các nhóm khác

- “Bảng kê đơn hàng bán” có ngày chứng từ, số chứng từ, khách hàng, nhân viên bán hàng, vật tư, nhóm vật tư, ĐVCS, giao dịch, trạng thái, nhóm theo đơn hàng và mẫu báo cáo.
- “Bảng kê đơn hàng mua” có nhà cung cấp, vật tư, các nhóm vật tư, trạng thái, nhóm theo đơn hàng và mẫu in số lượng/giá trị/nguyên tệ.
- “Báo cáo tình trạng đơn hàng mua” có cả ngày, giờ, ngày yêu cầu nhận, kho, vật tư, trạng thái và tùy chọn nhóm.
- Danh mục nhà cung cấp trong phiên UI hiển thị tổng 1.023 tại thời điểm khảo sát; chưa biết hết bộ lọc/ngầm định và phạm vi quyền nên không so sánh trực tiếp với 1.104 từng được AI trả lời.
- “Khai báo quy trình sản xuất sản phẩm” hiển thị mã cấu trúc, sản phẩm, version, quy trình, ĐVCS và trạng thái; chưa suy ra định mức BOM chỉ từ màn này.

## Hướng kết nối chatbot và cổng nghiệm thu

1. Lập danh sách tất cả menu, phân biệt nhóm/menu, màn thực tế, màn ngoài quyền và màn chưa mở; bổ sung screenshot/nhãn/cột và capture request/response chỉ đọc khi đã xác định an toàn.
2. Với từng báo cáo, xác minh liên kết UI → API → function/SQL → bảng/cột → grain, công thức, thời gian, trạng thái, đơn vị, quyền và định dạng. Không suy ra join hoặc chức năng từ trùng tên.
3. So sánh tối thiểu ba trường hợp cùng tài khoản, điều kiện lọc và thời điểm giữa UI, API và truy vấn DB độc lập; bổ sung ca rỗng, số âm, giới hạn trang, các trạng thái và quyền khác nhau. Đánh dấu rõ người xác nhận nghiệp vụ, ngày và phiên bản.
4. Từ các hợp đồng được duyệt, xây công cụ backend chỉ đọc, tham số hóa, kiểm soát quyền; model hiểu câu hỏi và trình bày. Kết quả cần phân biệt thành công, không có dòng, không quyền, thiếu điều kiện và lỗi.
5. Chạy thử qua đúng `htmp-nhanh` trên runtime, theo dõi phiên bản tool và so với ERP; chỉ phát hành từng nhóm sau khi đáp ứng bộ kiểm thử và nghiệm thu UI. Không suy kết quả thử nghiệm đơn lẻ thành hỗ trợ toàn bộ ERP/MES.

## Trạng thái

Đang khảo sát. Chưa mở/kiểm tra xong toàn bộ màn hình, chưa đối chiếu dữ liệu mẫu giữa UI–API–DB, chưa có xác nhận nghiệp vụ hay rollout chatbot dựa trên tài liệu này.
