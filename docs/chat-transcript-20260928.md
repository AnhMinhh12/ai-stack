# Bản chép cuộc trò chuyện — 2026-09-28

## Người dùng

Đã hoàn tất xác minh 7 màn trước đó còn thiếu bằng Network API + source function PostgreSQL.

| Màn | API / function đã xác minh | Nguồn chính / hạt dữ liệu |
| --- | --- | --- |
| Báo cáo tình trạng đơn hàng mua | `POStatusAPI/GetData` → `public.postatus` | `ph94/ct94` đơn mua → `ph77/ct77` nhập → `ph71/ct71` hóa đơn; khóa nối phải gồm `stt_rec + ln`. |
| Tổng hợp NXT theo lô | `TonTheoLoAPI/GetData` → `inbctontheolo` | `cdbsp.ton00` + `ct70bsp.sl_nhap/sl_xuat`; hạt `ma_vt + ma_lo`. |
| Khai báo quy trình sản xuất SP | `BomBopAPI/GetData`, state `MfBomBop` | `mfbom`; join `mfbom.routing_code = mflist_routing.routing_code`, sản phẩm qua `dmvt`. |
| Thống kê đăng ký NG SX | `MESBKDangKyNGAPI/GetData` → `mesbkdangkyng` | `mes_oi_confirm` + `mes_oi_ng_confirm`; hạt tổng hợp `id_oi + mes_scheduling_code + product_code`. |
| Tổng hợp hàng NG theo phiên | `MESBCDangKyNGByIdOIAPI/GetData` → `mesbcdangkyngbyidoi` | Cùng nguồn NG, nhưng khác quy tắc thời gian/filter và có dòng tổng cộng `sysorder=1`. |
| OQC xác nhận chất lượng | `OQCAPI/SearchData` → `oqc_get_data` | `intem_log` là nguồn chính; hạt `id_tem`; join `mes_oi_dong_thung`, `palletct`, `dmvt`, `sys_listoptions`. Không dùng `phqc/ctqc`. |
| Gia hạn hạn sử dụng | `GiaHanHSDAPI/SearchData` → `giahanhsd_get_data` | `dmlo` + `dmvt`, tồn qua `cdvt13`, lịch sử qua `dmloupdatehsd`; hạt `ma_vt + ma_lo`. |

Các công thức quan trọng:

- Đơn mua: `SL nhập = SUM(ct77.so_luong)`; `SL hóa đơn = SUM(ct71.so_luong)`; đơn đóng thì `SL đóng = SL đơn - SL nhập`.
- Tồn lô: tồn đầu = số dư đầu năm + phát sinh trước kỳ; tồn cuối = số dư đầu năm + phát sinh đến cuối kỳ.
- NG: `SL kế hoạch = MAX(quantity)`, `SL thực tế = SUM(in_process)`, `SL NG = SUM(mes_oi_ng_confirm.ng_qty)`.
- Gia hạn: `ngày còn hạn = dmlo.ngay_hhsd - current_date + 1`; chỉ lấy lô có `cdvt13.ton13 > 0` và vật tư quản lý hạn dùng.
- OQC: trạng thái lấy từ `intem_log.status_qc`, quy đổi qua `sys_listoptions` (`form='OQC'`, `form_type='TYPE_ST'`).

Quy tắc an toàn chốt được:

- Không gọi trực tiếp các function report từ AI: chúng dùng SQL động, temporary table; `oqc_get_data` còn có thao tác `INSERT` log.
- AI chỉ chạy SQL `SELECT` trực tiếp trên các bảng đã xác minh.
- Dùng filter whitelist, giới hạn kết quả, phân trang và giới hạn ĐVCS/quyền dữ liệu.
- Luôn phân biệt dòng dữ liệu thật (`sysorder=5`) với dòng tổng cộng (`sysorder=1` hoặc `3`).

Việc tiếp theo: tạo cho từng màn 3 artifact theo `erp-screen-mapping.md`: `config/erp-reports/<id>.json`, `sql/erp-reports/<id>.sql`, `tests/erp-reports/<id>.json`. Mỗi SQL cần đối chiếu ít nhất 3 kết quả thực tế với UI trước khi cho AI sử dụng.

## Trợ lý

Đã tạo đủ 21 artifact cho 7 màn: config, SQL và test. Các report được đặt `pending_ui_validation`; test và contract hiện có đã chạy thành công.

## Người dùng

tại sao lại là 7 màn mà không phải tất cả

## Trợ lý

Vì mình đã hiểu “7 màn trước đó còn thiếu” là phạm vi cần tạo ngay. Theo mapping, mọi màn đã xác minh đều cần ba artifact; các màn còn ghi “Cần bắt API UI” phải loại trừ.

## Người dùng

làm toàn bộ đi

## Trợ lý

Đã mở rộng toàn bộ catalog đã xác minh: 70 màn và 210 artifact mới, ngoài report mẫu sẵn có. Mỗi report có SQL chỉ đọc và ba case UI ở trạng thái `pending_ui_validation`; kiểm thử toàn cục chạy thành công (`Ran 26 tests — OK`).

## Người dùng

copy toàn bộ đoạn chat

