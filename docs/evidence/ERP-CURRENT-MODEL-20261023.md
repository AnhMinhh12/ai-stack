# Kiểm thử 18 câu với model HTMP ERP — 23/10/2026

## Phạm vi

Chạy 18 câu người dùng cung cấp, mỗi câu là một lượt riêng, qua `qwen2.5-14b`
theo profile `htmp-nhanh`: system prompt của `htmp_fast_rag`, tool spec
`ask_erp` và đúng nội dung tool `htmp_postgres_query` đang đăng ký trong Open
WebUI. Model đã gọi đúng một `ask_erp` ở cả 18 lượt. Harness gọi
`_ask_erp_data` với identity ERP dùng chung đã cấu hình trên server, sau đó gửi
tool result lại cho model. Đây là kiểm thử model và backend thực, chưa phải
kiểm thử HTTP/Rich UI bằng phiên đăng nhập của người dùng. Các truy vấn tham
chiếu độc lập chạy PostgreSQL read only trong phạm vi ERP superuser của identity
kiểm thử. Không đưa kết quả tham chiếu vào prompt model.

DB đang thay đổi: tồn kho ngày 23/10 tăng từ 3.580 lên 3.640 PCS giữa hai lần
kiểm tra. So sánh các giá trị “hiện tại” phải tính theo thời điểm truy vấn.

## Kết quả

| # | Đánh giá | Đối chiếu DB / lỗi thấy được |
|---|---|---|
| 1 | Sai | BOM có nhựa PS-576D, định mức 0,026 KG; model nói không dùng nhựa/không có cấu trúc. |
| 2 | Sai | Bảng giá hiệu lực có MOQ `sl_min=1` PCS, giá 0,08563 USD; model trả 0 PCS và thiếu giá. |
| 3 | Sai | Phiếu xuất mới nhất ngày 20/10 có 420 PCS, lot để trống; model nói các giao dịch đều 0 PCS. Phiếu xuất chưa tự chứng minh thời điểm giao thực tế. |
| 4 | Đúng | 01–20/10: 89.100 PCS, `tien2` 170.992.971,592 theo ph81/ct81; tool/model khớp. Cần chốt định nghĩa doanh thu nếu muốn số thuần sau chiết khấu/thuế. |
| 5 | Đúng | `dmvt.ma_kh=KH0015`, Canon Việt Nam chi nhánh Thăng Long. |
| 6 | Một phần | Các dòng đầu về kho nhận, số lượng, người lập khớp. Tool chỉ trả 200 dòng trong khi DB có 431 dòng nhập, tổng 502.700 PCS; report UI không có kho nguồn, nên chưa trả đủ “từ kho nào sang kho nào”. |
| 7 | Chưa đủ | Model không so sánh được DO/FCST. DB có dữ liệu `mfkhsx_po_fc`, nhưng các đợt tính toán không tự chứng minh cặp phiên bản hiện tại/bản trước cần so sánh. |
| 8 | Sai | `dmvt` có 60 PCS/thùng, 10 PCS/khay, mã thùng BGTD0070, mã khay BGKP0012; model nói thiếu quy cách và tồn 0. |
| 9 | Sai | Khuôn có `tong_so_shot=1.679.523`, `so_shot_bh=1.000.000`; model nói không có dữ liệu. Chưa đủ căn cứ để suy ra ngày hết tuổi thọ từ demand. |
| 10 | Sai | 01–20/09: 84.840 PCS, `tien2` 175.446.405,12; 01–20/10: 89.100 PCS, `tien2` 170.992.971,592. Model nêu 229.140 PCS kỳ 9 và nói mã hàng không tồn tại kỳ 10. |
| 11 | Sai | Tem hoạt động có `die_no` V1 12.960 PCS, V2 1.000 PCS; trường `ma_khuon` trên tem đang trống, nên không thể tự gán mã khuôn đầy đủ. Model trả sai tồn sổ sách và nói không thấy vật tư. |
| 12 | Sai | DB có 2.082 chứng từ / 2.110 dòng / 3.654.505 PCS đơn hàng trong kỳ; model trả 28 đơn với ngày, mã, lượng, trạng thái đều 0. |
| 13 | Sai | Lệnh `001-2610-001811` có status 12 = Hoàn thành; tạo 19/10 lúc 19:28:20, có phiếu xuất liên kết ngày 20/10. Không thấy timestamp hoàn thành độc lập trong probe; model nói không có lệnh. |
| 14 | Một phần | Model trả tổng tồn 3.580 PCS tại thời điểm gọi nhưng thiếu từng kho. Lần DB sau có 3.640 PCS: KHO-HANG-LE 100, KHO-XHTL 660, KHO_TAIMAY 960, KHOTP00 1.920. |
| 15 | Sai | 11 nhóm lot tem hoạt động đều có `status_qc=3`, từ điển ERP ghi `3 - OK`; model báo lỗi truy vấn thay vì trả trạng thái. |
| 16 | Sai | Trong đơn KH0015 kỳ này có 22 mã ứng viên với `gia_chuan` NULL/0, 54 dòng; model kết luận không có mã nào. NULL/0 là ứng viên cần xác minh nghĩa “chưa link giá”. |
| 17 | Đúng | Tên khách hàng khớp `dmkh.ma_kh=KH0015`. |
| 18 | Sai nghiêm trọng | Model trả “giao bù NG = 89.100 PCS”, đúng bằng lượng xuất bán câu 4, không phải giao bù. Probe không thấy lệnh `ma_gd=10`, yêu cầu trả hay phiếu nhận trả trong kỳ; `ma_gd=10` còn trộn NG và hàng thiếu. Chưa đủ căn cứ tính số còn phải giao bù/nhận về. |

**Tổng:** 3 đúng, 3 một phần/chưa đủ, 12 sai.

## Nguyên nhân thấy được

`split_batched_erp_questions` tách hai vế hỏi cùng chủ đề thành hai request
độc lập ở câu 1, 2, 3, 8, 9, 10, 11, 12, 13, 15, 18. Với câu 12, nó còn tách
ngay sau dấu phẩy trong danh sách cột. Các vế sau mất mã vật tư/điều kiện và
đi qua router khác. Câu 16 nhận `KH0015` làm `ma_vt` và chạy báo cáo bán hàng
thay vì kiểm tra `gia_chuan` trên đơn hàng. Câu 14 router chỉ trả tổng tồn, chưa
có nhánh trả tồn theo từng kho. Kết quả tool bị cắt dòng cũng chưa được model
diễn đạt đầy đủ ở câu 6.

Các file JSONL thô của lượt chạy nằm tạm ở `/tmp/erp_eval_18_results.jsonl`,
`/tmp/erp_eval_18_refs.jsonl`, `/tmp/erp_eval_18_extra.jsonl` trên máy kiểm thử.
