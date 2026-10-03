# Thiết kế bộ câu hỏi tra cứu giá vật tư và lịch sử mua

## 1. Mục tiêu

Chuẩn hóa cách chatbot trả lời các câu hỏi về mã vật tư, lịch sử đơn mua và
giá nhà cung cấp. Kết quả phải phân biệt rõ **đơn mua thực tế** với **báo giá
nhà cung cấp**; không được suy ra đã mua chỉ vì có mã vật tư hoặc có báo giá.

## 2. Nguồn dữ liệu và thuật ngữ

| Nghiệp vụ | Nguồn dữ liệu | Ý nghĩa trả lời |
| --- | --- | --- |
| Đã từng mua, số lần mua, giá mua lịch sử | `ph94` + `ct94` | Chỉ là đơn mua thực tế. Số lần mua = `count(distinct so_ct)`. |
| Giá danh mục NCC đang áp dụng | `dmgiamuact` | Giá theo mã vật tư, NCC và thời hạn hiệu lực. |
| Báo giá NCC và trạng thái duyệt | `phbgncc` + `ctbgncc` | Trả giá trước/sau VAT, hiệu lực, duyệt/đóng. Không gọi đây là lần mua. |
| Tên, ĐVT, loại vật tư | `dmvt` | Dùng để hiển thị/thẩm định mã; `gia_ton` không phải giá mua. |

Loại vật tư `41` (bán thành phẩm) và `51` (thành phẩm) là hàng công ty sản
xuất; không chọn chúng làm kết quả cho yêu cầu “lấy ngẫu nhiên một mã đã mua”.

Quy ước hiển thị:

- Giá mua gần nhất là **giá lịch sử trên đơn mua**, phải nêu ngày, số đơn, NCC,
  ĐVT và tiền tệ nếu có.
- Giá trước VAT và sau VAT là giá của danh mục/báo giá NCC, luôn kèm thuế suất,
  thời hạn hiệu lực và trạng thái duyệt.
- “Đã duyệt” đọc từ `ctbgncc.appr_yn`; `dmgiamuact.status` không thay thế trạng
  thái duyệt của phiếu báo giá.
- Nếu không tìm thấy dữ liệu, trả: “Chưa tìm thấy trong phạm vi dữ liệu/quyền
  được xem”; không khẳng định toàn công ty chưa có dữ liệu.

## 3. Quy tắc nhận diện mã vật tư

| Dạng nhập | Ví dụ | Kỳ vọng |
| --- | --- | --- |
| Mã chữ–số | `PC-3083` | Dùng đúng mã được nhập. |
| Mã số có nhãn | `mã 3003541` | Nhận `3003541`, không kế thừa mã trước đó. |
| Mã số đứng riêng | `3003541` | Nhận là mã vật tư khi người dùng chỉ gửi mã. |
| Mã chữ có dấu gạch ngang | `mã SIDE-PATRIA` | Nhận đúng `SIDE-PATRIA`. |
| Mã mới trong hội thoại | `thế còn mã SIDE-PATRIA` | Mã mới luôn ghi đè mã ngữ cảnh cũ. |

Không tự sửa mã. Ví dụ `303541` và `3003541` là hai mã khác nhau; nếu mã thứ
nhất không có dữ liệu thì phải trả kết quả rỗng, không tự thêm số `0`.

## 4. Bộ câu hỏi và kết quả bắt buộc

| ID | Câu hỏi mẫu | Ý định | Kết quả bắt buộc |
| --- | --- | --- | --- |
| Q01 | `Mã <MA_VT> đã từng mua chưa?` | Lịch sử mua | Có/không, `so_lan_dat`; dựa trên đơn mua thực tế. |
| Q02 | `Mã <MA_VT> mua bao nhiêu lần?` | Lịch sử mua | Số đơn mua khác nhau, lần đầu và lần gần nhất. |
| Q03 | `Mã <MA_VT> đã mua những lần nào?` | Lịch sử mua chi tiết | Ngày, số đơn, NCC, số lượng, ĐVT, tiền tệ, đơn giá và trạng thái; tối đa 50 dòng. |
| Q04 | `Giá mua gần nhất của mã <MA_VT> là bao nhiêu?` | Giá mua lịch sử | Giá, ĐVT, tiền tệ, ngày/số đơn và NCC của dòng đơn mua mới nhất. |
| Q05 | `Mã <MA_VT> giá thấp nhất, cao nhất và trung bình là bao nhiêu?` | Phân tích giá mua | Min, max, trung bình đơn giản và bình quân gia quyền; chỉ tính dòng giá lớn hơn 0. |
| Q06 | `Mã <MA_VT> có giá nào đang áp dụng?` | Giá danh mục NCC | Một giá hiệu lực mới nhất theo từng NCC; trước/sau VAT, thuế, ĐVT, hiệu lực. |
| Q07 | `Giá trước VAT và sau VAT của mã <MA_VT> là bao nhiêu?` | Giá NCC/báo giá | Giá trước VAT, sau VAT, thuế suất, ĐVT, NCC, hiệu lực, duyệt/đóng và nguồn giá. |
| Q08 | `Mã <MA_VT> đã được duyệt chưa?` | Duyệt báo giá | Báo giá NCC gần nhất, `da_duyet`, `da_dong`, số/ngày phiếu và giá trước/sau VAT. |
| Q09 | `Báo giá NCC <MA_NCC> của mã <MA_VT> còn hiệu lực không?` | Duyệt báo giá | Chỉ NCC yêu cầu; ngày bắt đầu/kết thúc, tình trạng hiệu lực, duyệt/đóng. |
| Q10 | `Mã <MA_VT> mua bao nhiêu lần và giá bao nhiêu?` | Lịch sử + giá | Số lần mua, các chỉ số giá mua lịch sử, giá mua gần nhất; kèm báo giá NCC gần nhất nếu có. |
| Q11 | `Mã <MA_VT> đã mua của nhà cung cấp nào?` | NCC đã mua | NCC, số đơn, lần đầu và lần gần nhất từ đơn mua thực tế. |
| Q12 | `Giá mua các lần của mã <MA_VT> thay đổi thế nào?` | Lịch sử giá | Danh sách theo thời gian; không gộp các tiền tệ khi chưa quy đổi tỷ giá. |
| Q13 | `Tổng tiền lần mua gần nhất của mã <MA_VT>?` | Giá trị đơn mua | Thành tiền VND và nguyên tệ của dòng đơn mua gần nhất. |

## 5. Kịch bản kiểm thử cụ thể

Các mã dưới đây là dữ liệu kiểm thử đã đối chiếu tại thời điểm tạo tài liệu;
giá có thể thay đổi sau khi NCC lập báo giá mới.

| Case | Câu hỏi gửi chat | Kết quả mong đợi cốt lõi |
| --- | --- | --- |
| T01 | `Mã 3003541 đã mua bao giờ chưa, mua bao nhiêu lần và giá?` | Mã được nhận là `3003541`; dùng `ph94/ct94`, không sinh SQL planner sai. Có 4 đơn mua trong phạm vi đang xem; giá gần nhất 21.636 VND/PCS. |
| T02 | `Mã 3003541 đã được duyệt chưa?` | Có báo giá NCC HTSS; giá hiện hành 21.636 VND/PCS trước và sau VAT, đã duyệt. |
| T03 | `Mã SIDE-PATRIA có giá bao nhiêu và đã mua bao nhiêu lần?` | Nhận mã chữ có gạch ngang, không lặp câu trả lời của mã trước; có 47 đơn mua; giá gần nhất 880 VND/PCS. |
| T04 | `Mã 303541 đã từng mua chưa?` | Không tự đổi sang `3003541`; nếu không có dữ liệu thì trả chưa tìm thấy trong phạm vi xem. |
| T05 | `Thế còn mã SIDE-PATRIA?` sau câu hỏi về `3003541` | `SIDE-PATRIA` phải ghi đè `3003541` và tạo một tool call mới. |
| T06 | `Giá trước VAT và sau VAT của SIDE-PATRIA tại NCC0346?` | Trước VAT 880, sau VAT 950 VND/PCS, VAT 8%, có ngày hiệu lực và trạng thái duyệt. |

## 6. Tiêu chí chấp nhận

Một ca được coi là đạt khi:

1. Mỗi câu hỏi ERP sinh một lần gọi `ask_erp` mới; không lặp lại kết quả lượt
   trước khi người dùng nêu mã mới.
2. `lookup.ma_vt` trong kết quả tool đúng nguyên văn mã người dùng nhập.
3. Câu hỏi lịch sử mua dùng `ph94 + ct94`, không dùng bảng tồn, `ct77`, hoặc
   báo giá để kết luận “đã mua”.
4. Câu hỏi giá có báo giá NCC phải hiển thị đủ giá trước VAT, sau VAT, ĐVT,
   NCC, hiệu lực và trạng thái duyệt.
5. Câu trả lời phân biệt “giá đơn mua lịch sử” với “báo giá NCC”; không gọi báo
   giá là một lần mua.
6. Không có dữ liệu thì không tự đoán/sửa mã vật tư và không kết luận ngoài
   phạm vi quyền truy cập.

## 7. Ràng buộc an toàn

- Không lấy `dmvt.gia_ton` để trả lời giá mua.
- Giá bằng 0 trong danh mục không phải là giá mua.
- Báo giá chưa duyệt phải ghi rõ “chờ duyệt”; báo giá không phải bằng chứng đã
  mua hoặc đã đặt hàng.
- Không thực hiện thao tác duyệt giá từ hội thoại; chức năng này chỉ tra cứu
  trạng thái.
