# Ánh xạ màn hình ERP sang nguồn dữ liệu

> Cập nhật: 2026-09-28. Nguồn kiểm chứng là catalog PostgreSQL ERP đang kết
> nối bằng tài khoản chỉ đọc, cấu hình `sys_command`/`sys_listinfo` và định
> nghĩa function report. Không dùng dữ liệu giao dịch trong quá trình lập tài
> liệu này.

## Cách đọc

- **Khóa chứng từ** `stt_rec`: khóa header do ERP cấu hình cho màn hình.
  Chi tiết chứng từ phải ghép theo `stt_rec`; khi cần định danh một dòng phải
  lấy thêm số dòng thực tế của bảng chi tiết, không dùng riêng `Số CT`.
- Các bảng `ph*` là header chứng từ, `ct*` là dòng chi tiết; `dm*` là danh
  mục. Tên hiển thị và ý nghĩa cột chuẩn là file
  [`danh-sach-bang-tra-cuu.md`](../danh-sach-bang-tra-cuu.md).
- **Đã xác minh** nghĩa là nguồn có trong `sys_listinfo` hoặc SQL function
  của chính report. **Cần bắt API UI** nghĩa là tên menu đã khớp nhưng DB chưa
  có state/function tương ứng; không được đoán SQL để đưa vào AI.

## Bán hàng

| Màn hình | State / function đã xác minh | Nguồn nghiệp vụ và khóa |
| --- | --- | --- |
| Đơn hàng (Hợp đồng) | `SO1`; `sobkdonhang` | `ph64` (header) + `ct64` (chi tiết), ghép `stt_rec`; tra `dmkh`, `dmvt`, `ctkhgh`. |
| Lệnh giao hàng | `TO2` | `ph96` (header) + `ct96`, `ctkhgh` (chi tiết), khóa UI `ph96.stt_rec`. |
| Phiếu xuất kho bán hàng | `HDA` | `ph81` + `ct81`, khóa UI `ph81.stt_rec`. |
| Bảng kê phiếu xuất kho bán hàng | `SOBKHoaDonBH`; `sobkhda` | `ph81`, `ct81`, `ctkhgh`, `ctlo`; tra `dmkh`, `dmvt`, `userinfo`. |
| Bảng kê lệnh giao hàng | `SOBKLenhGiaoHang`; `sobklenhgiaohang` | `ph96`, `ct96`, `ct96lo`, `ctkhgh`; tra `dmkh`, `dmvt`. |
| Báo cáo tiến độ giao hàng | `SOBCTienDoGH`; `sobctiendogh` | Chuỗi đơn–lệnh–xuất: `ph64/ct64`, `ph96/ct96/ctkhgh`, `ph81/ct81`; tra `dmkh`, `dmvt`, `sys_dmtt`, `userinfo`. |

## Mua hàng

| Màn hình | State / function đã xác minh | Nguồn nghiệp vụ và khóa |
| --- | --- | --- |
| Phiếu yêu cầu mua hàng | `PR0`; `pobkycmua` | `ph91` + `ct91`, khóa chứng từ `stt_rec`; report liên kết `ph94/ct94`, `ph77/ct77`, `ctkhnh`. |
| Đơn hàng mua | `PO1` | `ph94` + `ct94`, khóa UI `ph94.stt_rec`. |
| Phiếu yêu cầu nhập hàng | `YCN` | `phycn` + `ctycn`, khóa UI `phycn.stt_rec`; có liên kết `ph94/ct94`. |
| Phiếu nhập hàng | `PR1` | `ph77` + `ct77`, khóa UI `ph77.stt_rec`. |
| Bảng kê phiếu yêu cầu mua hàng | `POBKYCMua`; `pobkycmua` | `ph91/ct91`; các trạng thái đặt/nhập lấy từ `ph94/ct94`, `ph77/ct77`, `ctkhnh`; tra `dmvt`, `dmbp`, `dmkh`, `dmvv`. |
| Bảng kê đơn hàng mua | `POBKDonHang`; `pobkdonhang` | `ph94/ct94`; tra `dmvt`, `dmbp`, `dmkh`, `dmvv`, `userinfo`, `sys_dmtt`. |
| Bảng kê phiếu yêu cầu nhập hàng | `POBKYCNhap`; `pobkycnhap` | `phycn/ctycn`; liên kết `ph94/ct94`, `ph85`, `ct91`, `ct71`; tra danh mục vật tư/đối tác/bộ phận. |
| Bảng kê phiếu nhập hàng | `POBKNhap`; `pobknhap` | `ph77/ct77`; liên kết `ph94/ct94`, `ctycn`, `ctkhnh`, `ct71`; tra `dmvt`, `dmkh`, `dmbp`, `dmvv`. |
| Báo cáo tình trạng đơn hàng mua | Cần bắt API UI | Dự kiến cùng chuỗi `ph91/ct91 → ph94/ct94 → ph77/ct77`; phải xác minh function/API trước khi triển khai. |
| Báo cáo lịch sử thay đổi giá NCC | `POBCLSGia`; `pobclsgia` | `dmgiamua` + `dmgiamuact`; tra `dmvt`, `dmkh`. Khóa nghiệp vụ phải gồm mã vật tư, NCC và mốc hiệu lực giá. |

## Kho vận

| Màn hình | State / function đã xác minh | Nguồn nghiệp vụ và khóa |
| --- | --- | --- |
| Phiếu xuất kho | `PXA` | `ph84` + `ct84`, khóa UI `ph84.stt_rec`. |
| Phiếu nhập kho | `PND` | `ph74` + `ct74`, khóa UI `ph74.stt_rec`. |
| Phiếu yêu cầu nhập kho | `DNV` | `phdnv` + `ctdnv`, khóa UI `phdnv.stt_rec`. |
| Phiếu yêu cầu xuất kho | `DXV` | `phdxnvl` + `ctdxnvl`, khóa UI `phdxnvl.stt_rec`. |
| Danh mục sản phẩm, vật tư | `MfDmvt` | `dmvt`, khóa UI `ma_vt`. |
| Bảng kê phiếu nhập kho | `INBKNhapXuatKho`; `inbknhap_xuatkho` | `ph74/ct74`, giao dịch chuẩn hóa `ct70`; tra `dmvt`, `dmkh`, `dmbp`, `dmcp`, `dmcdgt`, `dmvv`, `userinfo`. |
| Bảng kê phiếu xuất kho | `INBKNhapXuatKho`; `inbknhap_xuatkho` | `ph84/ct84`, giao dịch chuẩn hóa `ct70`; cùng các bảng tra cứu của bảng kê nhập. |
| Bảng kê phiếu nhập, xuất điều chuyển | `InBKNhapXuatDC`; `inbknhap_xuatdc` | `ph85/ct85`, `ct70`, `ct70bsp`, `ctlo`; tra `dmvt`, `dmkh`, `userinfo`. |
| Bảng kê nhập xuất theo lô | `INBKNhapXuatTheoLo`; `inbknhapxuattheolo` | `ct70`, `ct70bsp`; nguồn chứng từ `ph74/ct77/ph84/ph85/ph88` và chi tiết tương ứng; tra `dmvt`, `dmkh`, `dmloainx`, `userinfo`. |
| Báo cáo tồn lô theo vị trí tất cả kho | `inbctonlotheovitri` | `ct70`, `ct70bsp`, `ctkk`, `cdbsp`; tra `dmvt`, `dmlo`, `dmkho`, `dmvitri`, `dmkh`. |
| Báo cáo tồn kho | `InBCTonKho`; `inbctonkho` | `ct70` là phát sinh; tra `dmvt`, `dmkho`, `dmnhvt`, `cdvt`. Chỉ số tồn là cột tính theo ngày chốt. |
| Báo cáo tồn theo kho | `InBCTonTheoKho`; `inbctontheokho` | `ct70`; tra `dmvt`, `dmkho`, `dmnhvt`, `cdvt`. Grain: vật tư + kho + ngày chốt. |
| Tổng hợp nhập xuất tồn | `InBCTHNXT`; `inbcthnxt` | `ct70` và `ct84`, tra `dmvt`, `dmkho`, `cdvt`; tồn đầu/phát sinh/tồn cuối là các giá trị tính. |
| Tổng hợp nhập xuất tồn theo lô | Cần bắt API UI | Dùng họ function tồn lô (`inbctontheolo`/`inbctonlotheokho`) nhưng chưa thấy state đúng tên trong cấu hình; phải xác minh endpoint. |

## Sản xuất và New model

| Màn hình | State / function đã xác minh | Nguồn nghiệp vụ và khóa |
| --- | --- | --- |
| Báo cáo cấu trúc sản phẩm | `MfBcCauTrucSP`; `mfbccautrucsp` | `mfbom` + `mfbom_material`; quan hệ phụ `mfbom_material_indirect`, `_replace`; tra `dmvt`. Khóa BOM: `bom_code`; dòng: `bom_code` + khóa dòng của chi tiết. |
| Danh mục cấu trúc sản phẩm | `MfBOM` | `mfbom` + `mfbom_material`, khóa UI `mfbom.bom_code`. |
| Khai báo quy trình sản xuất sản phẩm | `MfBomBop`; grid `BomBopAPI/GetData` | `mfbom`; UI grid exposes BOM, sản phẩm, version, routing, `branch_list` as Mã ĐVCS, and status. |
| Báo cáo lịch sử thay đổi bom list | `MfBKHistoryBomChange`; `mfbkhistorybomchange` | `history_bom_change`; liên kết ngữ cảnh BOM từ `mfbom`. Khóa lịch sử: ID/số thứ tự thay đổi + thời điểm, không phải riêng `bom_code`. |

## Kỹ thuật

| Màn hình | State / function đã xác minh | Nguồn nghiệp vụ và khóa |
| --- | --- | --- |
| Danh mục dây chuyền sản xuất | `MfListLine` | `mflist_line` + `mflist_line_station`, khóa UI `line_code`. |
| Danh mục khuôn | `ListDMKhuon` | `mfdmkhuon`, khóa UI `mold_code`; tra `dmhosokhuon`. |
| Danh mục nguyên nhân dừng máy | `ListNNDungMay` | `dmnndungmay`, khóa UI `ma_loi`. |
| Danh mục máy | `MfListMachine` | `mflist_machine`, khóa UI `machine_code`. |
| Hồ sơ khuôn | `DMHoSoKhuon` | `dmhosokhuon` + `dmhosokhuonsp`, khóa UI `ma_khuon`. |
| Báo cáo thông tin sản phẩm theo hồ sơ khuôn | `MESBCTTSPTHSK`; `mesbcttspthsk` | `dmhosokhuonsp`, `dmhosokhuon`, `dmvt`; khóa UI là cặp khuôn–sản phẩm. |
| Bảng kê lên khuôn | `MESBKThayKhuon`; `mesbkthaykhuon` | `mes_oi_van_hanh_khuon`, `_pause`, `mes_scheduling_output`; tra `dmvt`, `dmkh`, `dmloi`, `dmnndungmay`, `mflist_product_line_ct2`. |
| Bảng kê setup, vận hành máy | `MESBKSetup`; `mesbksetup` | `mes_oi_setup_may` + `_pause`; tra `dmvt`, `dmkh`, `dmnndungmay`, `dmdieukienep`. |
| Bảng kê phát sinh trong sản xuất | `MESBKPhatSinh`; `mesbkphatsinh` | `mes_oi_confirm`, `mes_oi_stop_line`, `mes_scheduling`, `mes_scheduling_output`; tra `dmvt`, `dmkh`, `dmloi`, `dmnndungmay`. |


## Điều hành sản xuất

| Màn hình | State / function | Nguồn DB |
| --- | --- | --- |
| Lệnh sản xuất | `PD1` | `phlsx` + `ctlsx`, `ctlsxvt`, `ctlsxqt`; khóa `phlsx.stt_rec`. |
| Lịch sản xuất (Import) | `WO2` | `mes_scheduling` + `mes_scheduling_output`; khóa `so_ct`. |
| Phân bổ thời gian dừng chuyền | `MESBKPhanBoTGDung`; `mesbkphanbotgdung` | `mes_oi_allocation_stop_line`, `mes_oi_confirm`, `new_oi_cbsx`, `dmnndungmay`. |
| Thống kê đăng ký NG | `MESBKDangKyNG` | Dữ liệu hạt phiên/OI từ `mes_oi_confirm` và phát sinh NG; cần trích function đúng state khi viết SQL. |
| Bảng kê NG linh kiện | `MESBKNGLinhKien`; `mesbknglinhkien` | `mes_oi_ng_materrial`, `mes_oi_material`, `mes_oi_confirm`, `dmvt`, `dmkh`, `dmloi`. |
| Thống kê cấp NVL | `MESBKCapNVL`; `mesbkcapnvl` | `mes_oi_material`, `mes_oi_material_prepare`, `mes_scheduling_output`, `ph84`, `dmvt`, `dmdvcs`. |
| Đóng gói, đóng thùng | `BKDGDT`; `bkdgdt` | `mes_oi_dong_thung`, `mes_oi_confirm`, `mes_scheduling`, `mes_scheduling_output`, `dmvt`. |
| Gộp, tách thùng | `MESBKGopTachThung`; `mesbkgoptachthung` | `intem_carton_log`, `intem_log`, `mes_oi_dong_thung`, `dmvt`, `dmdvcs`, `userinfo`. |
| Bảng kê Work Order | `MESBKWO`; `mesbkwo` | `mes_scheduling`, `mes_scheduling_output`, `mes_oi_confirm`, `dmvt`. |
| Bổ sung shot | `MESBKBoSungShot`; `mesbkbosungshot` | `mes_oi_add_quantity`, `dmvt`, `dmkh`. |
| Chi tiết bỏ shot | `MESBKCTBoShot`; `mesbkctboshot` | `mes_oi_bo_shot`, `mes_oi_material_history`, `dmvt`, `dmkh`. |
| Thay đổi cavity | `MESBKTDCavity`; `mesbktdcavity` | `mes_oi_change_cativity`, `mes_oi_confirm`, `dmvt`. |
| Nhân sự vận hành theo phiên | `MESBCNSVH`; `mesbcnsvh` | `mes_oi_nv_dung_may`, `mes_oi_confirm`, `new_oi_cbsx`, `mflist_line`, `userinfo`, `dmkh`. |
| Kết quả vận hành theo phiên | `MESBCKQVHPLV`; `mesbckqvhplv` | `mes_scheduling_output`, `mes_oi_confirm`, `mes_oi_stop_line`, `mes_oi_setup_may`, `mes_oi_add_quantity`, `mes_oi_ng_materrial`, `phlsx`, `ctlsx`, `dmvt`. |
| Tổng hợp hàng NG theo phiên | `MESBCDangKyNGByIdOI` | `mes_oi_confirm` và phát sinh NG; cần trích function trước khi tạo SQL. |
| Thời gian dừng chuyền theo phiên | `MfBCTGDC`; `mfbctgdc` | `mes_oi_stop_line`, `mes_oi_confirm`, `ctlsxvt`, `dmnndungmay`, `dmvt`, `dmkh`. |
| NVL dùng theo phiên/lô KH | `MfBCNVLByMaLoKH`; `mfbcnvlbymalokh` | `mes_oi_material`, `mes_oi_confirm`, `ctlsx`, `ctlsxvt`, `dmlo`, `dmvt`. |
| Version OI theo dây chuyền | `MESBCVersionOI`; `mesbcversionoi` | `mes_oi_version`, `mflist_line`, `mflist_line_station`. |
| Thu hồi NVL | `MESBCThuHoiNVL`; `mesbcthuhoinvl` | `mes_oi_material_history`, `mes_oi_confirm`, `mes_scheduling_output`, `new_oi_cbsx`. |

## Chất lượng

| Màn hình | State / function | Nguồn DB |
| --- | --- | --- |
| Danh mục bài kiểm tra | `QcDmChiTieu` | `qcdmchitieu`, khóa `ma_chi_tieu`. |
| Khai báo bài kiểm tra theo mã hàng | `QcDmVt` / `QcDmVtBTP` | `qcdmvt` + `qcdmvtct`; khóa ghép `ma_vt`, `step_code`, `ma_nh_chi_tieu`. |
| Phiếu IQC | `IQC` | `phiqc` + `ctiqc`, khóa `phiqc.stt_rec`. |
| Phiếu IPQC | `PQC` | `phpqc` + `ctpqc`, khóa `phpqc.stt_rec`. |
| OQC xác nhận chất lượng | `OQC` | State đã có; cần trích function/API để phân biệt `phqc/ctqc` với `phqcc/ctqcc`. |
| Gia hạn hạn sử dụng | `GiaHanHSD` | State và function `giahanhsd_get_data` đã có; cần trích nguồn bảng trước khi viết SQL. |
| Bảng kê IQC, IPQC | `QcBkIQCIPQC`; `qcbkiqcipqc` | `phiqc/ctiqc/ctiqcloi`, `phpqc/ctpqc/ctpqcloi`, `dmkh`, `dmvt`, `dmloi`, `qcdmchitieu`, `qcdmvtct`, `intem_log`. |
| Chi tiết bài kiểm tra theo mã hàng | `BKCTQCDmvt`; `bkctqcdmvt` | `qcdmvt/qcdmvtct`, `qcdmchitieu`, `dmvt`, `palletct`. |

## Việc triển khai tiếp theo

Tài liệu này là catalog nguồn cho toàn bộ danh sách. Để AI tra cứu được từng
màn hình, mỗi màn hình **đã xác minh** cần ba artifact versioned:

1. `config/erp-reports/<id>.json`: tên hiển thị, cột từ UI, alias tiếng Việt,
   filter được phép và metric.
2. `sql/erp-reports/<id>.sql`: SQL `SELECT` tham số hóa, chỉ đọc, sử dụng đúng
   nguồn/khóa phía trên.
3. `tests/erp-reports/<id>.json`: câu hỏi thật và expected result đã được
   người nghiệp vụ đối chiếu.

Màn hình đánh dấu **Cần bắt API UI** không được đưa vào planner SQL tự do.
Trước hết phải mở màn hình bằng tài khoản có quyền, ghi nhận endpoint/function
và xác nhận hạt dữ liệu (một chứng từ, một dòng, hay một snapshot theo ngày).
