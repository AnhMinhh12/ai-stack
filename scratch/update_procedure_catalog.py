"""Script to cleanly inject Stage 3 enterprise reports into erp_ai/procedure_catalog.py."""

import sys
from erp_ai.procedure_catalog import REPORT_CATALOG

# New enterprise reports across the 8 functional departments
NEW_REPORTS = {
    # -------------------------------------------------------------
    # 1. KHO & TỒN KHO (IN)
    # -------------------------------------------------------------
    "inbckstonkholo": {
        "id": "inbckstonkholo",
        "domain": "KHO",
        "procedure_name": "inbckstonkholo",
        "title": "Báo cáo kiểm soát tồn kho theo lô",
        "aliases": [
            "ton kho lo", "ton lo chua chi thi", "kiem soat lo ton", "ton theo lo", "inbckstonkholo"
        ],
        "description": "Kiểm soát chi tiết tồn kho theo từng số lô nhập, ngày hết hạn và số lượng khả dụng.",
        "default_params": {
            "dfrom": "", "dto": "", "cma_kho": "", "cma_vt": "", "cma_dvcs": "001",
            "cgroup_yn": "0", "cstatus": "*", "mau_bc": "001", "limit": 50, "offset": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "ma_vt": "Mã vật tư",
            "ten_vt": "Tên vật tư",
            "ma_lo": "Mã lô",
            "ma_kho": "Mã kho",
            "ton_cuoi": "Tồn cuối kỳ",
            "dvt": "ĐVT"
        },
        "summary_fields": ["ton_cuoi"]
    },

    "inbctrangthaikho": {
        "id": "inbctrangthaikho",
        "domain": "KHO",
        "procedure_name": None,
        "title": "Báo cáo trạng thái kho và sức chứa vị trí",
        "aliases": [
            "trang thai kho", "suc chua kho", "vi tri trong", "vi tri kho trong", "tinh trang vi tri"
        ],
        "description": "Tra cứu tổng hợp tình trạng sức chứa, số vị trí còn trống và phân bổ kệ/vị trí của từng kho.",
        "default_params": {},
        "column_labels": {
            "ma_kho": "Mã kho",
            "ten_kho": "Tên kho",
            "ma_vi_tri": "Vị trí / Kệ",
            "ma_vt": "Mã vật tư",
            "so_luong": "Tồn vị trí",
            "suc_chua": "Sức chứa tối đa"
        },
        "summary_fields": ["so_luong"]
    },

    # -------------------------------------------------------------
    # 2. BÁN HÀNG (SO)
    # -------------------------------------------------------------
    "dmbanggiact": {
        "id": "dmbanggiact",
        "domain": "BAN_HANG",
        "procedure_name": None,
        "title": "Bảng giá bán / Chính sách giá sản phẩm",
        "aliases": [
            "gia ban", "bang gia ban", "chinh sach gia", "don gia ban", "gia niem yet", "gia xuat ban"
        ],
        "description": "Tra cứu bảng giá bán và chính sách giá theo khách hàng hoặc sản phẩm cụ thể.",
        "default_params": {},
        "column_labels": {
            "ma_vt": "Mã sản phẩm",
            "ten_vt": "Tên sản phẩm",
            "ma_kh": "Mã khách hàng",
            "ten_kh": "Tên khách hàng",
            "gia_nt": "Đơn giá bán",
            "ngay_hl": "Ngày hiệu lực",
            "ma_nt": "Tiền tệ"
        },
        "summary_fields": []
    },

    "sobctonghopbh": {
        "id": "sobctonghopbh",
        "domain": "BAN_HANG",
        "procedure_name": "sobctonghopbh",
        "title": "Báo cáo tổng hợp bán hàng (tuần/tháng/doanh số)",
        "aliases": [
            "tong hop ban hang", "doanh so ban hang", "doanh thu ban hang", "tong hop doanh so", "sobctonghopbh"
        ],
        "description": "Tổng hợp doanh số, khối lượng xuất bán theo khách hàng, nhóm sản phẩm và khoảng thời gian.",
        "default_params": {
            "dfrom": "", "dto": "", "cma_kh": "", "cma_vt": "", "cma_dvcs": "001",
            "cgroup_yn": "1", "cstatus": "*", "mau_bc": "001", "limit": 50, "offset": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "ma_kh": "Mã KH",
            "ten_kh": "Tên khách hàng",
            "ma_vt": "Mã SP",
            "ten_vt": "Tên sản phẩm",
            "so_luong": "SL Bán",
            "tien": "Doanh số (VND)"
        },
        "summary_fields": ["so_luong", "tien"]
    },

    "sobkdubaotieuthu": {
        "id": "sobkdubaotieuthu",
        "domain": "BAN_HANG",
        "procedure_name": None,
        "title": "Bảng kê dự báo tiêu thụ (Forecast)",
        "aliases": [
            "du bao tieu thu", "du bao ban hang", "forecast", "du bao nhu cau", "sobkdubaotieuthu"
        ],
        "description": "Kế hoạch dự báo nhu cầu giao hàng và sản xuất theo tháng từ khách hàng.",
        "default_params": {},
        "column_labels": {
            "ma_fc": "Mã Forecast",
            "ma_kh": "Mã KH",
            "ma_vt": "Mã SP",
            "ngay_nhu_cau": "Ngày nhu cầu",
            "so_luong": "SL Dự báo"
        },
        "summary_fields": ["so_luong"]
    },

    "sobkbaogia": {
        "id": "sobkbaogia",
        "domain": "BAN_HANG",
        "procedure_name": None,
        "title": "Bảng kê giấy báo giá bán hàng",
        "aliases": [
            "bang ke bao gia", "bao gia khach hang", "giay bao gia", "sobkbaogia"
        ],
        "description": "Lịch sử và danh sách báo giá bán đã gửi cho khách hàng.",
        "default_params": {},
        "column_labels": {
            "so_ct": "Số báo giá",
            "ngay_ct": "Ngày báo giá",
            "ma_kh": "Mã KH",
            "ma_vt": "Mã SP",
            "gia": "Đơn giá chào",
            "status": "Trạng thái"
        },
        "summary_fields": []
    },

    # -------------------------------------------------------------
    # 3. MUA HÀNG (PO)
    # -------------------------------------------------------------
    "dmgiamuact": {
        "id": "dmgiamuact",
        "domain": "MUA_HANG",
        "procedure_name": None,
        "title": "Bảng giá mua nhà cung cấp (NCC)",
        "aliases": [
            "gia mua ncc", "bang gia mua", "gia nha cung cap", "chinh sach gia mua", "danh muc gia mua"
        ],
        "description": "Tra cứu bảng giá mua vật tư, hạt nhựa từ các nhà cung cấp theo thời hạn hiệu lực.",
        "default_params": {},
        "column_labels": {
            "ma_vt": "Mã vật tư",
            "ten_vt": "Tên vật tư",
            "ma_ncc": "Mã NCC",
            "ten_ncc": "Nhà cung cấp",
            "gia": "Đơn giá mua (VND)",
            "ngay_hl": "Ngày hiệu lực",
            "ngay_hh": "Ngày hết hạn",
            "ma_nt": "Tiền tệ"
        },
        "summary_fields": []
    },

    "pobkycnhap": {
        "id": "pobkycnhap",
        "domain": "MUA_HANG",
        "procedure_name": "pobkycnhap",
        "title": "Bảng kê phiếu yêu cầu nhập hàng (PR)",
        "aliases": [
            "yeu cau nhap", "phieu yeu cau nhap", "pr mua hang", "pr nhap", "pobkycnhap"
        ],
        "description": "Theo dõi các phiếu yêu cầu mua hàng / nhập hàng phát sinh từ phòng ban.",
        "default_params": {
            "dfrom": "", "dto": "", "cma_kh": "", "cma_vt": "", "cma_dvcs": "001",
            "cgroup_yn": "0", "cstatus": "*", "mau_bc": "001", "limit": 50, "offset": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "so_ct": "Số PR",
            "ngay_ct": "Ngày yêu cầu",
            "ma_vt": "Mã VT",
            "ten_vt": "Tên vật tư",
            "so_luong": "SL Yêu cầu",
            "ngay_giao": "Ngày cần hàng"
        },
        "summary_fields": ["so_luong"]
    },

    "pobkycmua": {
        "id": "pobkycmua",
        "domain": "MUA_HANG",
        "procedure_name": "pobkycmua",
        "title": "Bảng kê yêu cầu mua hàng",
        "aliases": [
            "yeu cau mua", "phieu yeu cau mua", "de nghi mua hang", "pobkycmua"
        ],
        "description": "Danh sách các đề nghị và yêu cầu mua hàng đang chờ phê duyệt hoặc đặt PO.",
        "default_params": {
            "dfrom": "", "dto": "", "cma_kh": "", "cma_vt": "", "cma_dvcs": "001",
            "cgroup_yn": "0", "cstatus": "*", "mau_bc": "001", "limit": 50, "offset": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "so_ct": "Số yêu cầu",
            "ngay_ct": "Ngày yêu cầu",
            "ma_vt": "Mã VT",
            "ten_vt": "Tên vật tư",
            "so_luong": "SL Mua",
            "dien_giai": "Lý do mua"
        },
        "summary_fields": ["so_luong"]
    },

    "pothnhap": {
        "id": "pothnhap",
        "domain": "MUA_HANG",
        "procedure_name": "pothnhap",
        "title": "Báo cáo tổng hợp hàng nhập mua theo NCC & vật tư",
        "aliases": [
            "tong hop nhap mua", "tong hop hang nhap ncc", "th nhap mua", "pothnhap"
        ],
        "description": "Tổng hợp khối lượng và giá trị nguyên vật liệu đã nhập mua từ các nhà cung cấp.",
        "default_params": {
            "dfrom": "", "dto": "", "cma_kh": "", "cma_vt": "", "cma_dvcs": "001",
            "cgroup_yn": "1", "cstatus": "*", "mau_bc": "001", "limit": 50, "offset": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "ma_kh": "Mã NCC",
            "ten_kh": "Nhà cung cấp",
            "ma_vt": "Mã VT",
            "ten_vt": "Tên vật tư",
            "so_luong": "Tổng SL Nhập",
            "tien": "Tổng giá trị (VND)"
        },
        "summary_fields": ["so_luong", "tien"]
    },

    # -------------------------------------------------------------
    # 4. KẾ TOÁN & TÀI CHÍNH (GL)
    # -------------------------------------------------------------
    "glso1": {
        "id": "glso1",
        "domain": "KE_TOAN",
        "procedure_name": None,
        "title": "Sổ cái tài khoản kế toán / Sổ chi tiết phát sinh theo tài khoản",
        "aliases": [
            "so cai", "so cai tai khoan", "so chi tiet tai khoan", "phat sinh tai khoan", "so phat sinh tk", "glso1", "so nhat ky chung"
        ],
        "description": "Sổ cái chi tiết các nghiệp vụ kế toán phát sinh của tài khoản (TK 111, 112, 131, 152, 154, 155, 331, 511, 621, 641, 642).",
        "default_params": {},
        "column_labels": {
            "ngay_ct": "Ngày hạch toán",
            "so_ct": "Số chứng từ",
            "dien_giai": "Diễn giải",
            "tk": "Tài khoản",
            "tk_du": "TK Đối ứng",
            "ps_no": "Phát sinh Nợ (VND)",
            "ps_co": "Phát sinh Có (VND)",
            "ma_kh": "Mã đối tác"
        },
        "summary_fields": ["ps_no", "ps_co"]
    },

    "glbccdsp": {
        "id": "glbccdsp",
        "domain": "KE_TOAN",
        "procedure_name": None,
        "title": "Bảng cân đối số phát sinh các tài khoản (Trial Balance)",
        "aliases": [
            "can doi phat sinh", "bang can doi phat sinh", "can doi so phat sinh", "cdps", "glbccdsp", "bang can doi tai khoan"
        ],
        "description": "Bảng tổng hợp cân đối số phát sinh Nợ và Có của toàn bộ hệ thống tài khoản kế toán trong kỳ.",
        "default_params": {},
        "column_labels": {
            "tk": "Số hiệu TK",
            "ten_tk": "Tên tài khoản",
            "tong_no": "Tổng phát sinh Nợ (VND)",
            "tong_co": "Tổng phát sinh Có (VND)"
        },
        "summary_fields": ["tong_no", "tong_co"]
    },

    "glsoctthuchi": {
        "id": "glsoctthuchi",
        "domain": "KE_TOAN",
        "procedure_name": None,
        "title": "Sổ quỹ tiền mặt và tiền gửi ngân hàng (TK 111 / 112)",
        "aliases": [
            "so quy", "so quy tien mat", "so tien gui", "thu chi", "so nhat ky thu chi", "thu chi tien mat", "glsoctthuchi"
        ],
        "description": "Nhật ký thu chi tiền mặt và dòng tiền gửi ngân hàng theo từng phiếu thu, phiếu chi, giấy báo có/báo nợ.",
        "default_params": {},
        "column_labels": {
            "ngay_ct": "Ngày chứng từ",
            "so_ct": "Số phiếu",
            "dien_giai": "Nội dung thu/chi",
            "tk": "Tài khoản",
            "tk_du": "TK Đối ứng",
            "thu": "Số tiền Thu (VND)",
            "chi": "Số tiền Chi (VND)"
        },
        "summary_fields": ["thu", "chi"]
    },

    "glbcchiphi": {
        "id": "glbcchiphi",
        "domain": "KE_TOAN",
        "procedure_name": None,
        "title": "Báo cáo tập hợp chi phí sản xuất và quản lý (TK 154 / 621 / 641 / 642)",
        "aliases": [
            "chi phi san xuat", "chi phi quan ly", "tap hop chi phi", "bao cao chi phi", "chi phi nvl", "chi phi tk 154", "glbcchiphi"
        ],
        "description": "Báo cáo tập hợp các khoản chi phí sản xuất kinh doanh dở dang, chi phí bán hàng và chi phí quản lý.",
        "default_params": {},
        "column_labels": {
            "tk": "Tài khoản chi phí",
            "ten_tk": "Tên loại chi phí",
            "chi_phi": "Chi phí tập hợp (VND)"
        },
        "summary_fields": ["chi_phi"]
    },

    # -------------------------------------------------------------
    # 5. SẢN XUẤT (MES)
    # -------------------------------------------------------------
    "mesbcoee": {
        "id": "mesbcoee",
        "domain": "SAN_XUAT",
        "procedure_name": "mesbcoee",
        "title": "Báo cáo hiệu suất thiết bị toàn phần OEE",
        "aliases": [
            "oee", "hieu suat thiet bi", "hieu suat oee", "ti le oee", "mesbcoee"
        ],
        "description": "Tính toán chỉ số OEE (Hiệu suất tổng thể thiết bị) bao gồm Sẵn sàng (A), Hiệu suất (P) và Chất lượng (Q).",
        "default_params": {
            "dfrom": "", "dto": "", "cma_line": "", "cma_dvcs": "001",
            "limit": 50, "offset": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "ma_line": "Mã Line/Máy",
            "a_rate": "Tỷ lệ Sẵn sàng (A)",
            "p_rate": "Hiệu suất (P)",
            "q_rate": "Chất lượng (Q)",
            "oee": "Chỉ số OEE (%)"
        },
        "summary_fields": []
    },

    "mesbksetup": {
        "id": "mesbksetup",
        "domain": "SAN_XUAT",
        "procedure_name": "mesbksetup",
        "title": "Bảng kê setup và vận hành máy",
        "aliases": [
            "setup may", "van hanh may", "cai dat may", "thoi gian setup", "mesbksetup"
        ],
        "description": "Nhật ký quá trình gá đặt khuôn, căn chỉnh thông số ép và chuẩn bị máy trước ca sản xuất.",
        "default_params": {
            "dfrom": "", "dto": "", "cma_line": "", "cma_dvcs": "001",
            "limit": 50, "offset": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "so_ct": "Số phiếu",
            "ngay_ct": "Ngày setup",
            "ma_line": "Mã máy",
            "ma_khuon": "Mã khuôn",
            "tg_setup": "Thời gian setup (phút)",
            "nguoi_setup": "KTV thực hiện"
        },
        "summary_fields": ["tg_setup"]
    },

    "mesbknglinhkien": {
        "id": "mesbknglinhkien",
        "domain": "SAN_XUAT",
        "procedure_name": "mesbknglinhkien",
        "title": "Bảng kê lỗi linh kiện NG trong sản xuất",
        "aliases": [
            "ng linh kien", "loi linh kien", "linh kien ng", "mesbknglinhkien"
        ],
        "description": "Theo dõi chi tiết phế phẩm và linh kiện hỏng phát sinh trực tiếp tại từng dây chuyền / máy ép.",
        "default_params": {
            "dfrom": "", "dto": "", "cma_line": "", "cma_vt": "", "cma_dvcs": "001",
            "limit": 50, "offset": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "so_ct": "Số chứng từ",
            "ngay_ct": "Ngày ghi nhận",
            "ma_vt": "Mã linh kiện",
            "ten_vt": "Tên linh kiện",
            "so_luong": "SL NG",
            "ly_do": "Nguyên nhân lỗi"
        },
        "summary_fields": ["so_luong"]
    },

    # -------------------------------------------------------------
    # 6. KẾ HOẠCH & ĐỊNH MỨC (MF)
    # -------------------------------------------------------------
    "mfbklsx": {
        "id": "mfbklsx",
        "domain": "KE_HOACH",
        "procedure_name": None,
        "title": "Bảng kê lệnh sản xuất (LSX)",
        "aliases": [
            "lenh san xuat", "lsx", "danh sach lenh san xuat", "ke hoach lsx", "mfbklsx"
        ],
        "description": "Danh sách lệnh sản xuất, số lượng giao khoán, đơn hàng khách hàng tương ứng và tiến độ hoàn thành.",
        "default_params": {},
        "column_labels": {
            "so_ct": "Số LSX",
            "ngay_ct": "Ngày lập",
            "ma_vt": "Mã sản phẩm",
            "ten_vt": "Tên sản phẩm",
            "dvt": "ĐVT",
            "so_luong": "SL Kế hoạch",
            "so_dh": "Đơn hàng (SO)",
            "ma_kh": "Khách hàng",
            "status": "Trạng thái"
        },
        "summary_fields": ["so_luong"]
    },

    "mfbkthongke": {
        "id": "mfbkthongke",
        "domain": "KE_HOACH",
        "procedure_name": "mfbkthongke",
        "title": "Bảng kê thống kê sản xuất theo kỳ",
        "aliases": [
            "thong ke san xuat", "thong ke sx", "tong hop san xuat", "mfbkthongke"
        ],
        "description": "Tổng hợp kết quả sản lượng hoàn thành và tỷ lệ phế phẩm theo từng lệnh sản xuất.",
        "default_params": {
            "dfrom": "", "dto": "", "cma_vt": "", "cma_dvcs": "001",
            "limit": 50, "offset": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "so_ct": "Số chứng từ",
            "ngay_ct": "Ngày thống kê",
            "ma_vt": "Mã SP",
            "so_luong": "SL Hoàn thành",
            "so_luong_ng": "SL Phế phẩm"
        },
        "summary_fields": ["so_luong", "so_luong_ng"]
    },

    "mfbctieuhaonvltheolsx": {
        "id": "mfbctieuhaonvltheolsx",
        "domain": "KE_HOACH",
        "procedure_name": "mfbctieuhaonvltheolsx",
        "title": "Báo cáo tiêu hao NVL theo lệnh sản xuất",
        "aliases": [
            "tieu hao nvl", "tieu hao theo lsx", "dinh muc tieu hao thuc te", "mfbctieuhaonvltheolsx"
        ],
        "description": "So sánh định mức nguyên vật liệu kế hoạch so với lượng xuất dùng thực tế trên mỗi lệnh sản xuất.",
        "default_params": {
            "dfrom": "", "dto": "", "cma_vt": "", "cma_dvcs": "001",
            "limit": 50, "offset": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "so_lsx": "Số LSX",
            "ma_vt_sp": "Mã SP",
            "ma_vt_nvl": "Mã NVL",
            "ten_vt_nvl": "Tên NVL",
            "sl_dinh_muc": "SL Định mức",
            "sl_thuc_te": "SL Thực xuất",
            "chenh_lech": "Chênh lệch"
        },
        "summary_fields": ["sl_dinh_muc", "sl_thuc_te"]
    },

    "mfbcthnxtcd": {
        "id": "mfbcthnxtcd",
        "domain": "KE_HOACH",
        "procedure_name": "mfbcthnxtcd",
        "title": "Báo cáo tổng hợp nhập xuất tồn công đoạn sản xuất",
        "aliases": [
            "nxt cong doan", "nhap xuat ton cong doan", "ton cong doan", "mfbcthnxtcd"
        ],
        "description": "Theo dõi lượng bán thành phẩm luân chuyển và tồn đọng tại từng trạm/công đoạn sản xuất.",
        "default_params": {
            "dfrom": "", "dto": "", "cma_vt": "", "cma_dvcs": "001",
            "limit": 50, "offset": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "ma_cd": "Công đoạn",
            "ma_vt": "Mã bán thành phẩm",
            "ten_vt": "Tên chi tiết",
            "ton_dau": "Tồn đầu",
            "nhap": "Nhập",
            "xuat": "Xuất",
            "ton_cuoi": "Tồn cuối"
        },
        "summary_fields": ["ton_dau", "nhap", "xuat", "ton_cuoi"]
    },

    # -------------------------------------------------------------
    # 7. CHẤT LƯỢNG (QC)
    # -------------------------------------------------------------
    "qcbkiqcipqc": {
        "id": "qcbkiqcipqc",
        "domain": "CHAT_LUONG",
        "procedure_name": None,
        "title": "Bảng kê phiếu kiểm tra IQC/IPQC chi tiết",
        "aliases": [
            "phieu iqc", "phieu ipqc", "kiem tra iqc", "kiem tra ipqc", "bien ban iqc", "qcbkiqcipqc"
        ],
        "description": "Chi tiết các biên bản đánh giá chất lượng nguyên liệu đầu vào và công đoạn ép nhựa.",
        "default_params": {},
        "column_labels": {
            "so_ct": "Số phiếu QC",
            "ngay_ct": "Ngày kiểm tra",
            "ma_vt": "Mã vật tư",
            "ten_vt": "Tên vật tư",
            "ma_ncc": "Nhà cung cấp",
            "so_luong_lo": "SL Lô kiểm",
            "sl_ok": "SL Đạt (OK)",
            "sl_ng": "SL Lỗi (NG)",
            "ket_luan": "Kết luận"
        },
        "summary_fields": ["so_luong_lo", "sl_ok", "sl_ng"]
    },

    "qcbcthloinvl": {
        "id": "qcbcthloinvl",
        "domain": "CHAT_LUONG",
        "procedure_name": "qcbcthloinvl",
        "title": "Báo cáo tổng hợp lỗi chỉ tiêu nguyên vật liệu",
        "aliases": [
            "tong hop loi nvl", "chi tieu loi nvl", "loi nguyen vat lieu", "qcbcthloinvl"
        ],
        "description": "Thống kê tần suất và tỷ lệ lỗi không đạt theo từng chỉ tiêu kỹ thuật của nguyên vật liệu.",
        "default_params": {
            "dfrom": "", "dto": "", "cma_vt": "", "cma_dvcs": "001",
            "limit": 50, "offset": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "ma_vt": "Mã vật tư",
            "ma_chi_tieu": "Chỉ tiêu kiểm định",
            "so_lan_loi": "Số lần lỗi",
            "tong_so": "Tổng số mẫu",
            "ti_le": "Tỷ lệ lỗi (%)"
        },
        "summary_fields": ["so_lan_loi", "tong_so"]
    },

    "qcbcthloitp": {
        "id": "qcbcthloitp",
        "domain": "CHAT_LUONG",
        "procedure_name": "qcbcthloitp",
        "title": "Báo cáo tổng hợp lỗi sản phẩm sản xuất (TP)",
        "aliases": [
            "tong hop loi tp", "loi thanh pham", "loi san pham", "qcbcthloitp"
        ],
        "description": "Thống kê các dạng lỗi xuất hiện trên thành phẩm xuất xưởng (ba-via, co ngót, biến dạng, trầy xước).",
        "default_params": {
            "dfrom": "", "dto": "", "cma_vt": "", "cma_dvcs": "001",
            "limit": 50, "offset": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "ma_vt": "Mã thành phẩm",
            "ma_chi_tieu": "Dạng lỗi",
            "so_lan_loi": "Số lần lỗi",
            "tong_so": "Tổng kiểm",
            "ti_le": "Tỷ lệ (%)"
        },
        "summary_fields": ["so_lan_loi", "tong_so"]
    },

    # -------------------------------------------------------------
    # 8. KHUÔN MẪU & THIẾT BỊ (VS)
    # -------------------------------------------------------------
    "dmhosokhuon": {
        "id": "dmhosokhuon",
        "domain": "KHUON_THIET_BI",
        "procedure_name": None,
        "title": "Danh mục hồ sơ kỹ thuật khuôn mẫu",
        "aliases": [
            "ho so khuon", "danh muc khuon", "thong so khuon", "cavity khuon", "kich thuoc khuon", "so shot bao tri", "dmhosokhuon"
        ],
        "description": "Tra cứu thông số kỹ thuật khuôn: số cavity, kích thước, tổng số shot dập và ngưỡng bảo trì.",
        "default_params": {},
        "column_labels": {
            "ma_khuon": "Mã khuôn",
            "ten_khuon": "Tên khuôn",
            "so_cavity": "Số Cavity",
            "tong_so_shot": "Tổng Shot dập",
            "so_shot_baotri": "Định mức bảo trì",
            "vi_tri_khuon": "Vị trí lưu",
            "status": "Trạng thái"
        },
        "summary_fields": ["tong_so_shot"]
    },

    "dmhosokhuonsc": {
        "id": "dmhosokhuonsc",
        "domain": "KHUON_THIET_BI",
        "procedure_name": None,
        "title": "Lịch sử bảo trì và sửa chữa khuôn mẫu",
        "aliases": [
            "sua chua khuon", "bao tri khuon", "lich su sua khuon", "nhat ky sua khuon", "dmhosokhuonsc"
        ],
        "description": "Nhật ký các đợt bảo dưỡng định kỳ, mài dao, phục hồi bề mặt và sửa chữa sự cố khuôn.",
        "default_params": {},
        "column_labels": {
            "ma_khuon": "Mã khuôn",
            "ngay_nhan_yc": "Ngày tiếp nhận",
            "loai": "Loại bảo trì",
            "noi_dung": "Nội dung hư hỏng / sửa chữa",
            "noi_sua": "Nơi sửa",
            "trang_thai": "Tình trạng"
        },
        "summary_fields": []
    },

    "mesbcttdskhuon": {
        "id": "mesbcttdskhuon",
        "domain": "KHUON_THIET_BI",
        "procedure_name": None,
        "title": "Báo cáo tình trạng bảo dưỡng khuôn định kỳ",
        "aliases": [
            "bao duong khuon", "tinh trang khuon", "canh bao bao tri khuon", "mesbcttdskhuon"
        ],
        "description": "Cảnh báo các bộ khuôn sắp chạm ngưỡng số shot bảo trì định kỳ để chuẩn bị kế hoạch dừng bảo dưỡng.",
        "default_params": {},
        "column_labels": {
            "ma_khuon": "Mã khuôn",
            "ten_khuon": "Tên khuôn",
            "tong_so_shot": "Shot hiện tại",
            "so_shot_baotri": "Ngưỡng bảo trì",
            "chenh_lech": "Số shot còn lại",
            "khuyen_nghi": "Khuyến nghị"
        },
        "summary_fields": []
    }
}

# Update REPORT_CATALOG in place
REPORT_CATALOG.update(NEW_REPORTS)
print(f"Total reports after update: {len(REPORT_CATALOG)}")

