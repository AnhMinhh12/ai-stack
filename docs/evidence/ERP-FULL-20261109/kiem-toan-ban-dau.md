# Kiểm thử mở rộng ngày 09/11/2026 — đang thực hiện

Dữ liệu trong `suite.json` là 76 câu hỏi nằm trong khối `text` của tài liệu câu hỏi, không đại diện toàn bộ tình huống ERP/MES. Các tệp `ui-results*.jsonl` lưu từng hội thoại, phản hồi và đầu vào/đầu ra công cụ được mở trên giao diện. `completed=true` chỉ có nghĩa giao diện dừng sinh, không có nghĩa kết quả đạt.

Trong thời gian thử, `GenericProcedureExecutor` được buộc `SET TRANSACTION READ ONLY` để hạn chế tác động DB. Một số procedure dùng DROP TABLE và bị từ chối; các kết quả đó phản ánh cấu hình thử này và không chứng minh báo cáo khi chạy ở cấu hình cũ thành công hoặc an toàn. Tài khoản DB không có quyền INSERT/UPDATE/DELETE trên các bảng public, không có quyền ghi sequence public; có một hàm SECURITY DEFINER có quyền thực thi, vì thế không coi chỉ riêng các kiểm tra đó là bằng chứng tất cả hàm đều an toàn. Không thực hiện phân quyền người dùng.

| ID trong suite | Nhận xét có bằng chứng | Trạng thái |
|---|---|---|
| 1 | Câu hỏi tồn hiện tại bị model tự đưa `date_as_of=2026-10-29`; tool `query_erp_report` báo `cannot execute DROP TABLE in a read-only transaction` từ `sys_getrolerecord`. | Sai tham số; không chạy được trong chế độ thử chỉ đọc |
| 2 | Chat hỏi thêm có muốn tất cả mã hay không dù câu hỏi yêu cầu toàn bộ kho; không thực hiện truy vấn. | Chưa trả lời |
| 3 | Câu hỏi tổng hợp nhập xuất không nêu mã/kho; model tự truyền `QC7-5146-000` và `KHO-IN`, trả lời không có chứng từ theo bộ lọc tự thêm. | Sai phạm vi |
| 5 | Hỏi sản lượng xuất bán theo tất cả khách hàng nhưng model chọn công cụ đơn bán và yêu cầu mã khách/mã vật tư. | Chưa trả lời đúng nghiệp vụ |
| 6 | Hỏi xuất kho theo ngày nhưng công cụ trả dòng đơn bán. | Sai loại dữ liệu; không coi là kết quả xuất bán |
| 39 | Lệnh 001-2610-001811: chat nêu 20/10/2026 21:34:57, trạng thái hoàn thành. Đối chiếu đọc `ph96`: status 12, date2 2026-10-20, time2 21:34:57.004248. | Khớp trường DB; ý nghĩa nghiệp vụ trạng thái và date2 cần xác nhận ERP |
| 40 | Tồn ngày 20/10/2026 nhưng công cụ trộn số dư theo ngày với vị trí/lô từ `cdvt13` hiện tại; câu trả lời có lô tháng 11. | Sai thời điểm thông tin vị trí/lô |
| 41 | Câu hỏi trạng thái lô tại 20/10; `lookup_qc_lot_status` không có tham số ngày và đọc tem đang hoạt động. | Thiếu bằng chứng cho thời điểm lịch sử; kết luận toàn bộ lô không có NG chưa được chứng minh |
| 42 | Hỏi các mã hàng chưa liên kết giá, chat trả số dòng đơn bán và không kiểm tra liên kết giá. | Chưa trả lời câu hỏi |
| 44 | Chat kết luận toàn bộ các chỉ tiêu giao bù và nhận NG bằng 0; một lần gọi dùng số đơn bịa `NG_RECEIVED` trong công cụ đơn bán rồi nhận không có dòng. Không có bằng chứng truy vấn đầy đủ giao bù và nhận NG. | Kết luận 0 không có căn cứ |


| 43 | `KH0015` và tên Canon Thăng Long khớp bản ghi `dmkh` được đọc. | Khớp trường DB đã kiểm tra |
| 47 | Đóng thùng QC7: công cụ cắt LIMIT 30, chatbot nói 30 thùng, 1.800 PCS như tổng; DB có 86.945 dòng theo mã, chưa lọc trạng thái/kỳ nghiệp vụ. | Không đầy đủ; không dùng 86.945 như số liệu nghiệp vụ đã duyệt |
| 50 | Hỏi lịch sử thay khuôn tháng 10, chatbot trả danh sách hồ sơ khuôn bất kỳ, không có sự kiện thay khuôn hay kỳ. | Sai loại báo cáo |
| 51 | Lệnh 001-2611-000004: chat nêu 02/11/2026 08:57:48; `ph96` có status 12, date2 2026-11-02, time2 08:57:48.196813. | Khớp trường DB; cần xác nhận ý nghĩa nghiệp vụ |

| 53 | Tra QC tem và kết luận không có lô bị khóa; công cụ chỉ tổng hợp `intem_log.status_qc` của tem hoạt động, chưa chứng minh kiểm tra trạng thái khóa lô. | Kết luận quá phạm vi dữ liệu đã kiểm tra |
| 54 | Hỏi cảnh báo hạn sử dụng nhưng chatbot trả thông tin chung sản phẩm và vị trí tồn, không đưa hạn sử dụng/cảnh báo. | Chưa trả lời |

| 57 | Giá ABS-260 50.244 VND, NCC0002, hiệu lực 16/10/2026–16/10/2027 khớp dòng `dmgiamuact`; chưa xác nhận toàn bộ điều kiện áp dụng. | Khớp trường DB đã kiểm tra |

| 25 | Mã ATSUMITEC KH0062 khớp `dmkh`. | Khớp trường DB đã kiểm tra |
| 58 | Hỏi sổ cái 1521 tháng 10, giao diện hiển thị các dòng 131 và kết luận không phát sinh; DB `ct00` có 9.304 dòng `tk=1521` cùng kỳ, `sum(ps_no)=sum(ps_co)=0` trong cột được kiểm tra. Chưa xác nhận trường tiền nghiệp vụ. | Sai tài khoản hiển thị; số phát sinh cần xác minh thêm |

| 32 | Thẻ kho QC7 ngày 01–20/10: chatbot tổng hợp 30 dòng (13.200 nhập, 17.400 xuất). DB `ct70` cùng mã và kỳ có 1.165 dòng; tổng thô 502.700 nhập, 504.990 xuất. | Tổng trên chat chỉ từ 30 dòng; số DB chưa xác nhận điều kiện chứng từ báo cáo |
| 59 | Sổ cái 131: giao diện cho 50 dòng rồi suy ra toàn bộ; DB `ct00` có 478 dòng tài khoản 131 trong kỳ, các cột `ps_no`/`ps_co` được kiểm tra đều bằng 0. | Thiếu dữ liệu; chưa xác nhận trường tiền nghiệp vụ |

| 36 | Chat so sánh QC7/KH0015: 84.840 và 89.100 PCS; `ph81`/`ct81` có đúng số lượng, `tien2` lần lượt 175.446.405,12 và 170.992.971,592 theo điều kiện source; các dòng đều KH0015, `ma_nt=USD`. Source khi có mã vật tư không lọc mã KH. | Khớp dữ liệu mẫu; lỗi bỏ điều kiện khách hàng tiềm ẩn, cần xác nhận tiền quy đổi và quy tắc trạng thái |
| 63 | Procedure thống kê sản xuất bị chặn DROP TABLE khi thử chỉ đọc; chatbot để lộ `<tool_call>` trong câu trả lời. | Không chạy được trong chế độ thử; lỗi hiển thị |

Danh mục màn hình lịch sử có 254 mục và tất cả đều còn `business_status=unverified`; không đồng nhất số câu hỏi đã chạy với số màn đã nghiệm thu. Chưa có phiên ERP trong CDP đợt này, vì vậy chưa đối chiếu được kết quả ERP trực tiếp. Cần đối chiếu nguồn DB, công thức, trạng thái, đơn vị và điều kiện theo từng câu trước khi kết luận đạt.

## Trạng thái lượt chạy

Đã thử 72/76 câu có mã trong bộ `suite.json`; 58 câu có phản hồi hoàn tất không chứa lỗi giao diện nhận diện được, 14 câu chưa hoàn tất hoặc gặp lỗi giao diện. Bốn câu 73–76 chưa chạy. Đây là số lượng thu thập, không phải số câu đạt. Phân loại từng câu và các câu còn thiếu nằm trong `theo-doi.csv`. Có chạy lại một phần các câu bị lỗi, tuy nhiên các tab thử bị chuyển về màn hình đăng nhập; không giả định nguyên nhân hết hạn phiên.

Sau khi dừng lượt thử, đã hoàn nguyên thay đổi tạm thời tại `generic_procedure_executor.py` và khởi động lại Open WebUI; container báo healthy. Các procedure vẫn chưa được chứng minh là chỉ đọc an toàn khi chạy dưới cấu hình cũ.
