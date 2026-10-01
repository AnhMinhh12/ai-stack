# Theo dõi xác minh UI report ERP/MES

Cập nhật: 30/09/2026. Đây là dashboard bền vững để tiếp tục ở chat mới.

- ✅ Đã xác minh UI đủ 3 case; cần đồng bộ lại manifest/test nếu trạng thái kỹ thuật còn `pending_ui_validation`.
- 🟡 Đang làm hoặc vướng lỗi UI.
- ⬜ Chưa xác minh UI.
- ◻️ Report vận hành, không thuộc danh sách 70 report cần 3 case UI.

Tổng: **70 report cần UI** — 14 hoàn tất, 2 đang vướng, 54 chưa làm. Có thêm 1 report vận hành ngoài danh sách.

| # | Report | ID | Trạng thái | Ghi chú/case gần nhất |
|---:|---|---|---|---|
| 1 | Bảng kê đơn hàng mua | `bang-ke-don-hang-mua` | ✅ | 001-2609-000659: 7 dòng, tổng 8,325; NCC0141/30-09: 3 dòng, tổng 40; 001-2609-000664: trạng thái Thực hiện 2 dòng/tổng 4,500 và lọc ngược GĐ duyệt trả 0. |
| 2 | Bảng kê IQC, IPQC | `bang-ke-iqc-ipqc` | ✅ | IQC POM9003/30-09-2026: 21 chỉ tiêu, mẫu/OK 0.1, NG 0; IPQC 16020859A/05-03-2026: 17 chỉ tiêu, mẫu/OK 4, NG 0; đổi cùng mẫu IPQC sang IQC trả 0 dòng. |
| 3 | Bảng kê lên khuôn | `bang-ke-len-khuon` | 🟡 | Lưới mặc định đã đối chiếu; lookup Số WO và tìm kiếm lưới không áp filter. |
| 4 | Bảng kê lệnh giao hàng | `bang-ke-lenh-giao-hang` | ✅ | 001-2609-002743: 4 vật tư/13 lô, tổng 21,078; lọc KH0045 vẫn chỉ lệnh này; đổi ngày giao sang 02-10 trả 0. |
| 5 | Bảng kê NG linh kiện | `bang-ke-ng-linh-kien` | 🟡 | Function `mesbknglinhkien` chỉ giữ cặp `id_oi + material_code + product_code` khớp `mes_oi_material`; hiện 0/57,238 phát sinh NG thỏa điều kiện nên UI rỗng. |
| 6 | Bảng kê phiếu nhập, xuất điều chuyển | `bang-ke-nhap-xuat-dieu-chuyen` | ✅ | 001-2610-000895: 12 dòng lô/tổng 29,020; lọc KHOTP03→KHO-GCN: thêm 001-2610-000906, 13 dòng/tổng 29,116; số phiếu xuất/nhập ĐC liên kết đúng. |
| 7 | Bảng kê nhập xuất theo lô | `bang-ke-nhap-xuat-theo-lo` | ⬜ | |
| 8 | Bảng kê phát sinh trong sản xuất | `bang-ke-phat-sinh-san-xuat` | ⬜ | |
| 9 | Bảng kê phiếu nhập hàng | `bang-ke-phieu-nhap-hang` | ⬜ | |
| 10 | Bảng kê phiếu nhập kho | `bang-ke-phieu-nhap-kho` | ⬜ | |
| 11 | Bảng kê phiếu xuất kho bán hàng | `bang-ke-phieu-xuat-kho-ban-hang` | ⬜ | |
| 12 | Bảng kê phiếu xuất kho | `bang-ke-phieu-xuat-kho` | ⬜ | |
| 13 | Bảng kê phiếu yêu cầu mua hàng | `bang-ke-phieu-yeu-cau-mua-hang` | ⬜ | |
| 14 | Bảng kê phiếu yêu cầu nhập hàng | `bang-ke-phieu-yeu-cau-nhap-hang` | ⬜ | |
| 15 | Bảng kê setup, vận hành máy | `bang-ke-setup-van-hanh-may` | ✅ | Setup DUC-0024; setup có pause DUC-0246/A1; filter lưới DUC-0246. |
| 16 | Bảng kê Work Order | `bang-ke-work-order` | ⬜ | |
| 17 | Báo cáo cấu trúc sản phẩm | `bao-cao-cau-truc-san-pham` | ✅ | 425-00122; PC-0757; công đoạn CD_DUC. |
| 18 | Báo cáo lịch sử thay đổi BOM list | `bao-cao-lich-su-thay-doi-bom` | ✅ | 425-00187-1, 10–30/09; hai lần thay đổi PC-0757. |
| 19 | Báo cáo lịch sử thay đổi giá NCC | `bao-cao-lich-su-thay-doi-gia-ncc` | ⬜ | |
| 20 | Báo cáo thông tin SP theo hồ sơ khuôn | `bao-cao-thong-tin-sp-theo-ho-so-khuon` | ✅ | Đã xác nhận trước đó. |
| 21 | Báo cáo tiến độ giao hàng | `bao-cao-tien-do-giao-hang` | ⬜ | |
| 22 | Báo cáo tình trạng đơn hàng mua | `bao-cao-tinh-trang-don-hang-mua` | ⬜ | |
| 23 | Báo cáo tồn kho | `bao-cao-ton-kho` | ⬜ | |
| 24 | Báo cáo tồn lô theo vị trí tất cả kho | `bao-cao-ton-lo-theo-vi-tri-kho` | ⬜ | |
| 25 | Báo cáo tồn theo kho | `bao-cao-ton-theo-kho` | ⬜ | |
| 26 | Bổ sung shot | `bo-sung-shot` | ⬜ | |
| 27 | Chi tiết bài kiểm tra theo mã hàng | `chi-tiet-bai-kiem-tra-theo-ma-hang` | ⬜ | |
| 28 | Chi tiết bỏ shot | `chi-tiet-bo-shot` | ⬜ | |
| 29 | Danh mục bài kiểm tra | `danh-muc-bai-kiem-tra` | ⬜ | |
| 30 | Danh mục cấu trúc sản phẩm | `danh-muc-cau-truc-san-pham` | ✅ | 425-00122; biến thể V2; BOM Không sử dụng bị loại. |
| 31 | Danh mục dây chuyền sản xuất | `danh-muc-day-chuyen-san-xuat` | ✅ | DC-HTSS-01 + station/máy; DC_HOT-0001; DUC-0249 bị loại. |
| 32 | Danh mục khuôn | `danh-muc-khuon` | ✅ | FE3-V374; K_FE3; khuôn Không sử dụng bị loại. |
| 33 | Danh mục máy | `danh-muc-may` | ⬜ | |
| 34 | Danh mục nguyên nhân dừng máy | `danh-muc-nguyen-nhan-dung-may` | ⬜ | |
| 35 | Danh mục sản phẩm, vật tư | `danh-muc-san-pham-vat-tu` | ⬜ | |
| 36 | Đơn hàng (Hợp đồng) | `don-hang-hop-dong` | ⬜ | |
| 37 | Đơn hàng mua | `don-hang-mua` | ⬜ | |
| 38 | Đóng gói, đóng thùng | `dong-goi-dong-thung` | ⬜ | |
| 39 | Gia hạn hạn sử dụng | `gia-han-han-su-dung` | ⬜ | |
| 40 | Gộp, tách thùng | `gop-tach-thung` | ⬜ | |
| 41 | Hồ sơ khuôn | `ho-so-khuon` | ✅ | K_VGP1A098-G3 có 24 SP; FE3-V377 hiển thị cả hai trạng thái. |
| 42 | Kết quả vận hành theo phiên | `ket-qua-van-hanh-theo-phien` | ⬜ | |
| 43 | Khai báo bài kiểm tra theo mã hàng | `khai-bao-bai-kiem-tra-theo-ma-hang` | ⬜ | |
| 44 | Khai báo quy trình sản xuất SP | `khai-bao-quy-trinh-san-xuat-sp` | ✅ | Đã xác nhận trước đó. |
| 45 | Lệnh giao hàng | `lenh-giao-hang` | ⬜ | |
| 46 | Lệnh sản xuất | `lenh-san-xuat` | ⬜ | |
| 47 | Lịch sản xuất (Import) | `lich-san-xuat-import` | ⬜ | |
| 48 | Nhân sự vận hành theo phiên | `nhan-su-van-hanh-theo-phien` | ⬜ | |
| 49 | Nhật ký nhập xuất tồn | `nhat-ky-nhap-xuat-ton` | ◻️ | Report vận hành đã deploy, ngoài 70 report UI. |
| 50 | NVL dùng theo phiên/lô KH | `nvl-dung-theo-phien-lo-kh` | ⬜ | |
| 51 | OQC xác nhận chất lượng | `oqc-xac-nhan-chat-luong` | ⬜ | |
| 52 | Phân bổ thời gian dừng chuyền giữa các phiên | `phan-bo-thoi-gian-dung-chuyen` | ✅ | Case A1/B1 đã khớp trước đó. |
| 53 | Phiếu IPQC | `phieu-ipqc` | ⬜ | |
| 54 | Phiếu IQC | `phieu-iqc` | ⬜ | |
| 55 | Phiếu nhập hàng | `phieu-nhap-hang` | ⬜ | |
| 56 | Phiếu nhập kho | `phieu-nhap-kho` | ⬜ | |
| 57 | Phiếu xuất kho bán hàng | `phieu-xuat-kho-ban-hang` | ⬜ | |
| 58 | Phiếu xuất kho | `phieu-xuat-kho` | ⬜ | |
| 59 | Phiếu yêu cầu mua hàng | `phieu-yeu-cau-mua-hang` | ⬜ | |
| 60 | Phiếu yêu cầu nhập hàng | `phieu-yeu-cau-nhap-hang` | ⬜ | |
| 61 | Phiếu yêu cầu nhập kho | `phieu-yeu-cau-nhap-kho` | ⬜ | |
| 62 | Phiếu yêu cầu xuất kho | `phieu-yeu-cau-xuat-kho` | ⬜ | |
| 63 | Thay đổi cavity | `thay-doi-cavity` | ⬜ | |
| 64 | Thời gian dừng chuyền theo phiên | `thoi-gian-dung-chuyen-theo-phien` | ⬜ | |
| 65 | Thống kê cấp NVL | `thong-ke-cap-nvl` | ⬜ | |
| 66 | Thống kê đăng ký NG SX | `thong-ke-dang-ky-ng-sx` | ⬜ | |
| 67 | Thu hồi NVL | `thu-hoi-nvl` | ⬜ | |
| 68 | Tổng hợp hàng NG theo phiên | `tong-hop-hang-ng-theo-phien` | ⬜ | |
| 69 | Tổng hợp nhập xuất tồn | `tong-hop-nhap-xuat-ton` | ⬜ | |
| 70 | Tổng hợp NXT theo lô | `tong-hop-nxt-theo-lo` | ⬜ | |
| 71 | Version OI theo dây chuyền | `version-oi-theo-day-chuyen` | ⬜ | |

## Quy tắc cập nhật

Sau mỗi report, cập nhật một dòng ở bảng này, rồi đồng bộ ba artifact `config/erp-reports/`, `sql/erp-reports/` và `tests/erp-reports/`. Khi mở chat mới, đọc file này trước để chọn report 🟡 hoặc ⬜ tiếp theo.
