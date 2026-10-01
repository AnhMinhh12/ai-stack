# Hướng dẫn xác minh UI cho từng màn ERP

> Cập nhật: 2026-09-28. Phạm vi là 70 report có trạng thái
> `pending_ui_validation`. Mỗi report chỉ được chuyển sang `validated` khi cả
> ba mẫu bên dưới khớp UI theo cùng một tài khoản, cùng ĐVCS và cùng thời điểm
> chốt dữ liệu.

## Quy trình dùng cho mọi màn

1. Mở đúng màn bằng tài khoản nghiệp vụ có quyền. Lưu ảnh/export UI, tên ĐVCS,
   người dùng, thời điểm chạy và toàn bộ điều kiện lọc.
2. Chạy file `sql/erp-reports/<id>.sql` bằng tài khoản **read-only**, với đúng
   tham số UI. Không gọi function report; không chạy SQL có ghi dữ liệu.
3. So khớp số dòng trước, rồi so khớp từng cột hiển thị, dòng tổng cộng và
   phân trang. Dùng khóa dòng của màn (không chỉ số chứng từ).
4. Điền kết quả thực tế, khóa/mẫu đã dùng và ảnh/export vào
   `tests/erp-reports/<id>.json`. Chỉ đổi `status` khi 3/3 mẫu đạt.

Mẫu 1 phải là truy vấn phổ biến có dữ liệu; mẫu 2 phải có tình huống biên; mẫu
3 phải kiểm tra một filter hoặc một quan hệ/join quan trọng. Nếu UI có tổng
cộng, kiểm tra dòng dữ liệu thật riêng với tổng cộng. Nếu có phân quyền/ĐVCS,
luôn kiểm tra bằng một ĐVCS được phép và một trường hợp không được phép.

## Bán hàng

| Màn / ID | Khóa và nguồn phải kiểm | Ba mẫu bắt buộc trên UI |
| --- | --- | --- |
| Đơn hàng (Hợp đồng) / `don-hang-hop-dong` | `ph64.stt_rec` + dòng `ct64`; tra `dmkh`, `dmvt` | (1) Một đơn nhiều dòng; (2) lọc khách hàng và khoảng ngày; (3) dòng có lịch giao/`ctkhgh`. |
| Lệnh giao hàng / `lenh-giao-hang` | `ph96.stt_rec` + `ct96`; liên kết `ctkhgh` | (1) Một lệnh nhiều dòng; (2) lọc ngày giao; (3) lệnh có/không có liên kết đơn. |
| Phiếu xuất kho bán hàng / `phieu-xuat-kho-ban-hang` | `ph81.stt_rec` + `ct81` | (1) Phiếu nhiều vật tư; (2) lọc kho/khách; (3) phiếu có đơn vị tính hoặc lô khác nhau. |
| Bảng kê phiếu xuất kho bán hàng / `bang-ke-phieu-xuat-kho-ban-hang` | Dòng `ct81`, liên kết `ctkhgh`, `ctlo` | (1) Một ngày có nhiều phiếu; (2) lọc khách hàng; (3) dòng có lô và người lập. |
| Bảng kê lệnh giao hàng / `bang-ke-lenh-giao-hang` | Dòng `ct96`, `ct96lo`, `ctkhgh` | (1) Một lệnh nhiều dòng; (2) lọc thời gian; (3) đối chiếu số lượng giao theo lô. |
| Báo cáo tiến độ giao hàng / `bao-cao-tien-do-giao-hang` | Chuỗi `ct64 → ct96 → ct81`; khóa nối chứng từ/dòng | (1) Đơn giao một phần; (2) đơn đã giao đủ; (3) lọc khách hoặc hạn giao, so các số lượng đơn–lệnh–xuất. |

## Mua hàng

| Màn / ID | Khóa và nguồn phải kiểm | Ba mẫu bắt buộc trên UI |
| --- | --- | --- |
| Phiếu yêu cầu mua hàng / `phieu-yeu-cau-mua-hang` | `ph91.stt_rec` + `ct91` | (1) Phiếu nhiều dòng; (2) lọc bộ phận/ngày; (3) dòng đã/ chưa tạo đơn mua. |
| Đơn hàng mua / `don-hang-mua` | `ph94.stt_rec` + `ct94` | (1) Đơn nhiều dòng; (2) lọc NCC/thời gian; (3) đơn có nhận hàng một phần. |
| Phiếu yêu cầu nhập hàng / `phieu-yeu-cau-nhap-hang` | `phycn.stt_rec` + `ctycn` | (1) Phiếu nhiều dòng; (2) lọc NCC; (3) dòng liên kết đơn mua. |
| Phiếu nhập hàng / `phieu-nhap-hang` | `ph77.stt_rec` + `ct77` | (1) Phiếu nhiều dòng; (2) lọc kho/NCC; (3) dòng có chênh lệch với số đặt. |
| Bảng kê phiếu yêu cầu mua hàng / `bang-ke-phieu-yeu-cau-mua-hang` | `ct91`, đối chiếu liên kết `ct94`, `ct77` | (1) Yêu cầu chưa đặt; (2) đã đặt một phần; (3) đã nhập, kiểm tra trạng thái và số lượng. |
| Bảng kê đơn hàng mua / `bang-ke-don-hang-mua` | `ct94`, tra NCC/vật tư/bộ phận | (1) Đơn nhiều dòng; (2) lọc NCC; (3) kiểm tra người lập, ngày và trạng thái. |
| Bảng kê phiếu yêu cầu nhập hàng / `bang-ke-phieu-yeu-cau-nhap-hang` | `ctycn`, liên kết `ct94`, `ph85`, `ct71` | (1) Yêu cầu có đơn mua; (2) có điều chuyển; (3) có hóa đơn, đối chiếu liên kết. |
| Bảng kê phiếu nhập hàng / `bang-ke-phieu-nhap-hang` | `ct77`, liên kết `ct94`, `ctycn`, `ct71` | (1) Nhập nhiều dòng; (2) lọc NCC/kỳ; (3) đối chiếu số đặt, số nhập và hóa đơn. |
| Báo cáo tình trạng đơn hàng mua / `bao-cao-tinh-trang-don-hang-mua` | Hạt `ct94.stt_rec + ln`; chuỗi `ct94 → ct77 → ct71` | (1) Nhập một phần; (2) đơn đóng, kiểm `SL đóng = SL đơn − SL nhập`; (3) hóa đơn một phần, kiểm SUM nhập/hóa đơn. **Đồng thời lưu endpoint/API UI vì mapping cũ chưa được cập nhật.** |
| Báo cáo lịch sử thay đổi giá NCC / `bao-cao-lich-su-thay-doi-gia-ncc` | `dmgiamua/dmgiamuact`; vật tư + NCC + ngày hiệu lực | (1) Một cặp vật tư/NCC nhiều lần đổi giá; (2) lọc ngày hiệu lực; (3) giá hiện hành và giá hết hiệu lực. |

## Kho vận

| Màn / ID | Khóa và nguồn phải kiểm | Ba mẫu bắt buộc trên UI |
| --- | --- | --- |
| Phiếu xuất kho / `phieu-xuat-kho` | `ph84.stt_rec` + `ct84` | (1) Phiếu nhiều dòng; (2) lọc kho/ngày; (3) phiếu có lô hoặc đối tượng nhận. |
| Phiếu nhập kho / `phieu-nhap-kho` | `ph74.stt_rec` + `ct74` | (1) Phiếu nhiều dòng; (2) lọc kho/ngày; (3) nguồn nhập khác nhau. |
| Phiếu yêu cầu nhập kho / `phieu-yeu-cau-nhap-kho` | `phdnv.stt_rec` + `ctdnv` | (1) Phiếu nhiều dòng; (2) lọc kho/bộ phận; (3) yêu cầu đã/chưa thực hiện. |
| Phiếu yêu cầu xuất kho / `phieu-yeu-cau-xuat-kho` | `phdxnvl.stt_rec` + `ctdxnvl` | (1) Phiếu nhiều dòng; (2) lọc bộ phận; (3) yêu cầu có xuất một phần. |
| Danh mục sản phẩm, vật tư / `danh-muc-san-pham-vat-tu` | `dmvt.ma_vt` | (1) Mã có dấu/nhóm; (2) lọc nhóm vật tư; (3) vật tư ngưng sử dụng hoặc thiếu thuộc tính. |
| Bảng kê phiếu nhập kho / `bang-ke-phieu-nhap-kho` | Dòng `ct74`, phát sinh `ct70` | (1) Một ngày nhiều phiếu; (2) lọc kho; (3) kiểm mã giao dịch, người lập và tổng số lượng. |
| Bảng kê phiếu xuất kho / `bang-ke-phieu-xuat-kho` | Dòng `ct84`, phát sinh `ct70` | (1) Một ngày nhiều phiếu; (2) lọc kho; (3) kiểm mã giao dịch, người nhận và tổng. |
| Bảng kê phiếu nhập, xuất điều chuyển / `bang-ke-nhap-xuat-dieu-chuyen` | `ph85/ct85`, `ct70`, `ct70bsp`, `ctlo` | (1) Điều chuyển một kho; (2) có lô; (3) đối chiếu kho đi/kho đến và dấu số lượng. |
| Bảng kê nhập xuất theo lô / `bang-ke-nhap-xuat-theo-lo` | `ct70`, `ct70bsp`; grain vật tư + lô + phát sinh | (1) Lô có nhập; (2) cùng lô có xuất; (3) lọc vật tư/lô, đối chiếu chứng từ gốc. |
| Báo cáo tồn lô theo vị trí tất cả kho / `bao-cao-ton-lo-theo-vi-tri-kho` | Vật tư + lô + kho + vị trí; `ct70/ct70bsp/ctkk/cdbsp` | (1) Lô tại một vị trí; (2) cùng lô nhiều vị trí; (3) ngày chốt, đối chiếu tồn với UI. |
| Báo cáo tồn kho / `bao-cao-ton-kho` | Vật tư + kho + ngày chốt; `ct70`, `cdvt` | (1) Một vật tư một kho; (2) nhiều kho; (3) đổi ngày chốt, kiểm tồn đầu/nhập/xuất/tồn cuối. |
| Báo cáo tồn theo kho / `bao-cao-ton-theo-kho` | Grain vật tư + kho + ngày chốt | (1) Một kho; (2) lọc nhóm vật tư; (3) nhiều kho, kiểm không gộp sai kho. |
| Tổng hợp nhập xuất tồn / `tong-hop-nhap-xuat-ton` | `ct70`, `ct84`, `cdvt` | (1) Kỳ có cả nhập/xuất; (2) kỳ không phát sinh nhưng có tồn đầu; (3) kiểm công thức tồn cuối. |
| Tổng hợp nhập xuất tồn theo lô / *(chưa có artifact)* | Cần xác minh endpoint và grain theo lô trước | (1) Bắt Network khi chạy UI; (2) xác nhận filter kỳ/kho/lô; (3) so endpoint với function tồn lô. Không tạo SQL/cho AI dùng trước khi hoàn tất. |

## Sản xuất, kỹ thuật và điều hành

| Màn / ID | Khóa và nguồn phải kiểm | Ba mẫu bắt buộc trên UI |
| --- | --- | --- |
| Báo cáo cấu trúc sản phẩm / `bao-cao-cau-truc-san-pham` | `mfbom.bom_code` + dòng `mfbom_material` | (1) BOM một cấp; (2) BOM có vật tư gián tiếp/thay thế; (3) lọc mã thành phẩm, kiểm số lượng và đơn vị. |
| Danh mục cấu trúc sản phẩm / `danh-muc-cau-truc-san-pham` | `mfbom.bom_code` | (1) BOM đang hiệu lực; (2) BOM ngưng hiệu lực; (3) BOM nhiều vật tư, kiểm không nhân dòng header. |
| Khai báo quy trình sản xuất SP / `khai-bao-quy-trinh-san-xuat-sp` | `mfbom`, `mflist_routing`, `dmvt`; BOM + routing | (1) Một thành phẩm có routing; (2) lọc thành phẩm; (3) routing nhiều công đoạn. **Lưu endpoint/API UI do mapping cũ đánh dấu cần bắt.** |
| Báo cáo lịch sử thay đổi BOM list / `bao-cao-lich-su-thay-doi-bom` | ID/số thứ tự lịch sử + thời điểm | (1) Một BOM nhiều lần thay đổi; (2) lọc khoảng thời gian; (3) kiểm ai thay đổi/nội dung thay đổi. |
| Danh mục dây chuyền sản xuất / `danh-muc-day-chuyen-san-xuat` | `mflist_line.line_code` | (1) Dây chuyền có nhiều station; (2) lọc trạng thái; (3) kiểm station thuộc đúng line. |
| Danh mục khuôn / `danh-muc-khuon` | `mfdmkhuon.mold_code` | (1) Khuôn đang hoạt động; (2) lọc loại khuôn; (3) khuôn liên kết hồ sơ. |
| Danh mục nguyên nhân dừng máy / `danh-muc-nguyen-nhan-dung-may` | `dmnndungmay.ma_loi` | (1) Mã nguyên nhân; (2) lọc nhóm; (3) trạng thái sử dụng/ngưng. |
| Danh mục máy / `danh-muc-may` | `mflist_machine.machine_code` | (1) Máy có line/station; (2) lọc line; (3) máy ngưng hoạt động. |
| Hồ sơ khuôn / `ho-so-khuon` | `dmhosokhuon.ma_khuon` + dòng SP | (1) Hồ sơ một SP; (2) nhiều SP; (3) lọc khuôn, kiểm quan hệ khuôn–SP. |
| Báo cáo thông tin SP theo hồ sơ khuôn / `bao-cao-thong-tin-sp-theo-ho-so-khuon` | Khuôn + SP + phiên/kết quả | (1) Một khuôn một SP; (2) khuôn nhiều SP; (3) đối chiếu máy/line và kết quả sản xuất. |
| Bảng kê lên khuôn / `bang-ke-len-khuon` | `mes_oi_van_hanh_khuon` + phiên | (1) Lên khuôn bình thường; (2) có pause; (3) lọc ngày/line, kiểm thời lượng và nguyên nhân. |
| Bảng kê setup, vận hành máy / `bang-ke-setup-van-hanh-may` | `mes_oi_setup_may` + pause | (1) Setup hoàn tất; (2) có pause; (3) lọc máy/line, kiểm thời gian. |
| Bảng kê phát sinh trong sản xuất / `bang-ke-phat-sinh-san-xuat` | `mes_oi_confirm` + phiên/output | (1) Có xác nhận sản lượng; (2) có dừng chuyền; (3) lọc ngày/line, kiểm không nhân dữ liệu. |
| Lệnh sản xuất / `lenh-san-xuat` | `phlsx.stt_rec` + `ctlsx/ctlsxvt/ctlsxqt` | (1) Lệnh nhiều thành phẩm/NVL; (2) lọc ngày/line; (3) kiểm quy trình và NVL liên quan. |
| Lịch sản xuất (Import) / `lich-san-xuat-import` | `mes_scheduling.so_ct` + output | (1) Một lịch nhiều output; (2) lọc ngày/line; (3) lịch hủy/đổi phiên. |
| Phân bổ thời gian dừng chuyền / `phan-bo-thoi-gian-dung-chuyen` | Allocation + `id_oi` | (1) Một dừng một nguyên nhân; (2) một dừng phân bổ nhiều nguyên nhân; (3) tổng thời gian phân bổ bằng UI. |
| Thống kê đăng ký NG / `thong-ke-dang-ky-ng-sx` | `id_oi + mes_scheduling_code + product_code` | (1) Một phiên có NG; (2) nhiều xác nhận cùng phiên; (3) kiểm `MAX(quantity)`, `SUM(in_process)`, `SUM(ng_qty)`. |
| Bảng kê NG linh kiện / `bang-ke-ng-linh-kien` | Phát sinh `mes_oi_ng_materrial` + vật tư | (1) Một dòng NG; (2) nhiều linh kiện cùng phiên; (3) lọc sản phẩm/nguyên nhân. |
| Thống kê cấp NVL / `thong-ke-cap-nvl` | `mes_oi_material` + prepare/output | (1) Cấp đủ; (2) cấp một phần; (3) liên kết phiếu xuất kho, kiểm ĐVCS. |
| Đóng gói, đóng thùng / `dong-goi-dong-thung` | Thùng/tem + `mes_oi_dong_thung` | (1) Một thùng; (2) nhiều thùng cho một phiên; (3) lọc sản phẩm, kiểm số lượng đóng gói. |
| Gộp, tách thùng / `gop-tach-thung` | Nhật ký `intem_carton_log`, tem/thùng | (1) Gộp thùng; (2) tách thùng; (3) kiểm chuỗi thùng trước/sau và người thao tác. |
| Bảng kê Work Order / `bang-ke-work-order` | `mes_scheduling` + output/confirm | (1) Work Order có output; (2) nhiều phiên; (3) lọc ngày/line, kiểm kế hoạch so thực tế. |
| Bổ sung shot / `bo-sung-shot` | `mes_oi_add_quantity` + phiên/vật tư | (1) Một lần bổ sung; (2) nhiều lần cùng phiên; (3) lọc khách hàng/sản phẩm. |
| Chi tiết bỏ shot / `chi-tiet-bo-shot` | `mes_oi_bo_shot` + history | (1) Một dòng bỏ; (2) nhiều lý do; (3) đối chiếu vật tư/khách hàng và số shot. |
| Thay đổi cavity / `thay-doi-cavity` | `mes_oi_change_cativity` + phiên | (1) Một lần đổi; (2) nhiều lần trong phiên; (3) kiểm cavity trước/sau và thời gian. |
| Nhân sự vận hành theo phiên / `nhan-su-van-hanh-theo-phien` | Nhân sự + `id_oi` | (1) Một người/phiên; (2) nhiều người/phiên; (3) lọc line, kiểm không nhân thời gian. |
| Kết quả vận hành theo phiên / `ket-qua-van-hanh-theo-phien` | Output + `id_oi` | (1) Phiên hoàn tất; (2) có setup/dừng/NG; (3) kiểm các chỉ số sản lượng/tổn thất. |
| Tổng hợp hàng NG theo phiên / `tong-hop-hang-ng-theo-phien` | `id_oi + mes_scheduling_code + product_code`; `sysorder` | (1) Dòng thật `sysorder=5`; (2) dòng tổng `sysorder=1`; (3) lọc sản phẩm/khoảng thời gian. |
| Thời gian dừng chuyền theo phiên / `thoi-gian-dung-chuyen-theo-phien` | Stop line + `id_oi` | (1) Một lần dừng; (2) nhiều lý do; (3) lọc line/ngày, kiểm tổng thời gian. |
| NVL dùng theo phiên/lô KH / `nvl-dung-theo-phien-lo-kh` | Vật tư + lô KH + `id_oi` | (1) Một lô KH; (2) nhiều NVL; (3) lọc lô, kiểm số lượng dùng. |
| Version OI theo dây chuyền / `version-oi-theo-day-chuyen` | Version + line/station | (1) Một line; (2) nhiều station; (3) phiên bản thay đổi theo thời gian. |
| Thu hồi NVL / `thu-hoi-nvl` | `mes_oi_material_history` + phiên/output | (1) Một lần thu hồi; (2) nhiều lần cùng phiên; (3) kiểm số lượng thu hồi và ĐVCS. |

## Chất lượng

| Màn / ID | Khóa và nguồn phải kiểm | Ba mẫu bắt buộc trên UI |
| --- | --- | --- |
| Danh mục bài kiểm tra / `danh-muc-bai-kiem-tra` | `qcdmchitieu.ma_chi_tieu` | (1) Chỉ tiêu hoạt động; (2) lọc nhóm; (3) chỉ tiêu ngưng dùng. |
| Khai báo bài kiểm tra theo mã hàng / `khai-bao-bai-kiem-tra-theo-ma-hang` | `ma_vt + step_code + ma_nh_chi_tieu` | (1) Một mã hàng một bước; (2) nhiều chỉ tiêu; (3) lọc mã hàng/bước, kiểm không nhân dòng. |
| Phiếu IQC / `phieu-iqc` | `phiqc.stt_rec` + `ctiqc` | (1) Phiếu nhiều chỉ tiêu; (2) có lỗi; (3) lọc NCC/ngày, kiểm kết quả. |
| Phiếu IPQC / `phieu-ipqc` | `phpqc.stt_rec` + `ctpqc` | (1) Phiếu nhiều chỉ tiêu; (2) có lỗi; (3) lọc sản phẩm/phiên. |
| OQC xác nhận chất lượng / `oqc-xac-nhan-chat-luong` | `intem_log.id_tem`; status qua `sys_listoptions` | (1) Một tem có trạng thái QC; (2) kiểm quy đổi `status_qc`; (3) lọc vật tư, kiểm thùng/pallet. **Lưu endpoint/UI để khép khác biệt với mapping cũ.** |
| Gia hạn hạn sử dụng / `gia-han-han-su-dung` | `ma_vt + ma_lo`; `dmlo`, `cdvt13`, lịch sử | (1) Lô tồn dương còn hạn; (2) lô hết hạn; (3) lô vừa gia hạn, kiểm `ngày còn hạn = ngày HHSD − ngày chạy + 1`. |
| Bảng kê IQC, IPQC / `bang-ke-iqc-ipqc` | Dòng IQC/IPQC + lỗi/chỉ tiêu | (1) IQC có lỗi; (2) IPQC có lỗi; (3) lọc kỳ/loại QC, kiểm không trộn hai loại. |
| Chi tiết bài kiểm tra theo mã hàng / `chi-tiet-bai-kiem-tra-theo-ma-hang` | `qcdmvt/qcdmvtct` + chỉ tiêu | (1) Một mã hàng; (2) nhiều chỉ tiêu; (3) có pallet/step, kiểm thứ tự hiển thị. |

## Điều kiện chấp nhận và cập nhật trạng thái

- Không có sai lệch số dòng, cột, tổng số lượng/giá trị, đơn vị, trạng thái,
  ngày hoặc dữ liệu ngoài ĐVCS/quyền được phép.
- Mỗi case ghi `ui_filter`, `ui_export_or_screenshot`, `sql_parameters`,
  `expected_result`, `actual_result`, người xác nhận và thời điểm.
- Sai lệch phải được phân loại: nguồn thiếu, khóa join sai, filter khác UI,
  quy tắc tổng cộng, timezone/ngày chốt hoặc phân quyền. Sửa SQL/config rồi
  chạy lại cả ba case.
- Chỉ thay `pending_ui_validation` bằng `validated` sau khi người nghiệp vụ
  ký nhận. Đến lúc đó mới đưa ID vào allowlist của AI.
