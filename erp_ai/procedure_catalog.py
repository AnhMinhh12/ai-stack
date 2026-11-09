"""Catalog of standard ERP 3S & MES report procedures and queries.

This catalog establishes a declarative contract for business reports across
all domains (Inventory, Sales, Purchasing, AR/AP, Quality, MES/MF).
"""

from typing import Any, Callable, Dict, List, Optional


REPORT_CATALOG: Dict[str, Dict[str, Any]] = {
    # -------------------------------------------------------------
    # 1. KHO & TỒN KHO (INVENTORY - IN)
    # -------------------------------------------------------------
    "inbcthnxt": {
        "id": "inbcthnxt",
        "domain": "KHO",
        "procedure_name": "inbcthnxt",
        "title": "Báo cáo tổng hợp Nhập - Xuất - Tồn kho",
        "aliases": [
            "nhap xuat ton", "nxt", "tong hop nhap xuat ton", "xuat nhap ton",
            "bien dong kho", "sl nhap xuat", "tong hop kho"
        ],
        "description": "Tổng hợp lượng tồn đầu kỳ, nhập, xuất và tồn cuối kỳ của vật tư theo kho hoặc toàn công ty.",
        "default_params": {
            "time_to": "23:59",
            "cma_kho": "",
            "cma_vt": "",
            "cnh_vt1": "", "cnh_vt2": "", "cnh_vt3": "", "cnh_vt4": "", "cnh_vt5": "", "cnh_vt6": "", "cnh_vt7": "",
            "ctk_vt": "",
            "cma_dvcs": "001",
            "cgroup": "",
            "in_tong_sl": "1",
            "cstatus": "*",
            "mau_bc": "",
            "gridid": "",
            "limit": 50,
            "offset": 0,
            "culture": "vi-VN"
        },
        "column_labels": {
            "ma_vt": "Mã vật tư",
            "ten_vt": "Tên vật tư",
            "dvt": "ĐVT",
            "ton_dau": "Tồn đầu kỳ",
            "sl_nhap": "SL Nhập",
            "sl_xuat": "SL Xuất",
            "ton_cuoi": "Tồn cuối kỳ",
            "du_dau": "Giá trị đầu kỳ (VND)",
            "tien_nhap": "Giá trị nhập (VND)",
            "tien_xuat": "Giá trị xuất (VND)",
            "du_cuoi": "Giá trị cuối kỳ (VND)"
        },
        "summary_fields": ["ton_dau", "sl_nhap", "sl_xuat", "ton_cuoi", "du_cuoi"]
    },

    "inbctonkho": {
        "id": "inbctonkho",
        "domain": "KHO",
        "procedure_name": "inbctonkho",
        "title": "Báo cáo tồn kho tức thời / theo ngày",
        "aliases": [
            "ton kho", "so luong ton", "kiem tra ton", "con bao nhieu", "ton bao nhieu",
            "hang ton", "muc ton", "bao cao ton kho", "ton thuc te"
        ],
        "description": "Số lượng tồn kho thực tế tính đến thời điểm tra cứu hoặc theo ngày chỉ định.",
        "default_params": {
            "cma_kho": "",
            "cma_vt": "",
            "cnh_vt1": "", "cnh_vt2": "", "cnh_vt3": "", "cnh_vt4": "", "cnh_vt5": "",
            "ctk_vt": "",
            "cma_dvcs": "001",
            "cgroup": "loai_vt",
            "mau_bc": "001",
            "gridid": "InBCTonKho1",
            "limit": 50,
            "offset": 0,
            "culture": "vi-VN"
        },
        "column_labels": {
            "ma_vt": "Mã vật tư",
            "ten_vt": "Tên vật tư",
            "ma_kho": "Kho",
            "so_luong": "SL Tồn",
            "dvt": "ĐVT",
            "tien": "Giá trị tồn (VND)"
        },
        "summary_fields": ["so_luong", "tien"]
    },

    "inbctontheokho": {
        "id": "inbctontheokho",
        "domain": "KHO",
        "procedure_name": "inbctontheokho",
        "title": "Báo cáo tồn kho phân bổ theo từng kho",
        "aliases": [
            "ton theo kho", "ton tung kho", "phan bo kho", "ton kho theo kho",
            "cac kho con bao nhieu", "ton kho nao", "o kho nao"
        ],
        "description": "Phân bổ số lượng tồn kho của một mã hàng tại từng kho cụ thể (Kho TP, Kho NVL, Kho Lắp ráp...).",
        "default_params": {
            "cma_kho": "",
            "cma_vt": "",
            "cma_dvcs": "001",
            "mau_bc": "001",
            "limit": 50,
            "offset": 0,
            "culture": "vi-VN"
        },
        "column_labels": {
            "ma_vt": "Mã vật tư",
            "ten_vt": "Tên vật tư",
            "ma_kho": "Mã kho",
            "ten_kho": "Tên kho",
            "so_luong": "SL Tồn",
            "dvt": "ĐVT"
        },
        "summary_fields": ["so_luong"]
    },

    "inbctontheovitri": {
        "id": "inbctontheovitri",
        "domain": "KHO",
        "procedure_name": "inbctontheovitri",
        "title": "Báo cáo tồn kho theo vị trí",
        "aliases": [
            "ton theo vi tri", "vi tri ton", "o vi tri nao", "vi tri kho",
            "nam o dau", "vi tri tai kho", "vi tri", "vi tri o kho", "kho tai may o vi tri nao"
        ],
        "description": "Chi tiết số lượng tồn kho của từng mã vật tư phân bổ theo từng vị trí cụ thể (kệ, tầng, máy, pallet) trong kho.",
        "default_params": {
            "cma_kho": "",
            "cma_vt": "",
            "cma_vi_tri": "",
            "cma_kh": "",
            "cnh_vt1": "", "cnh_vt2": "", "cnh_vt3": "", "cnh_vt4": "", "cnh_vt5": "", "cnh_vt6": "", "cnh_vt7": "",
            "ctk_vt": "",
            "cma_dvcs": "001",
            "cstatus": "*",
            "cgroup": "1",
            "cdieu_chuyen": "1",
            "mau_bc": "001",
            "gridid": "InBCTonTheoVitri1",
            "culture": "vi-VN"
        },
        "column_labels": {
            "ma_vt": "Mã vật tư",
            "ten_vt": "Tên vật tư",
            "dvt": "ĐVT",
            "ma_vi_tri": "Mã vị trí",
            "ten_vi_tri": "Tên vị trí",
            "ton_dau": "Tồn đầu",
            "sl_nhap": "Nhập",
            "sl_xuat": "Xuất",
            "ton_cuoi": "Tồn cuối"
        },
        "summary_fields": ["ton_cuoi"]
    },

    "inso1": {
        "id": "inso1",
        "domain": "KHO",
        "procedure_name": None,  # Handled directly via public.ct70 in native_tools
        "title": "Thẻ kho / Sổ chi tiết biến động vật tư",
        "aliases": [
            "the kho", "so chi tiet vat tu", "lich su nhap xuat", "bien dong vat tu",
            "chung tu kho", "nhap xuat the nao", "phieu nhap kho", "phieu xuat kho"
        ],
        "description": "Chi tiết từng phiếu nhập (PNF) và phiếu xuất (PXB) phát sinh của một mã vật tư.",
        "column_labels": {
            "ngay_ct": "Ngày CT",
            "so_ct": "Số chứng từ",
            "ma_ct": "Loại CT",
            "ma_kho": "Kho",
            "dien_giai": "Diễn giải",
            "sl_nhap": "SL Nhập",
            "sl_xuat": "SL Xuất"
        },
        "summary_fields": ["sl_nhap", "sl_xuat"]
    },

    "bccanhbaohsd": {
        "id": "bccanhbaohsd",
        "domain": "KHO",
        "procedure_name": "bccanhbaohsd",
        "title": "Báo cáo cảnh báo hạn sử dụng lô / vật tư",
        "aliases": [
            "han su dung", "hsd", "sap het han", "canh bao han", "qua han",
            "het han", "tuoi tho lo", "lo het han"
        ],
        "description": "Danh sách các lô nguyên vật liệu hoặc thành phẩm sắp hết hạn hoặc đã quá hạn.",
        "default_params": {
            "cma_kho": "",
            "cma_vt": "",
            "cma_lo": "",
            "cma_dvcs": "001",
            "limit": 50,
            "offset": 0,
            "culture": "vi-VN"
        },
        "column_labels": {
            "ma_vt": "Mã vật tư",
            "ten_vt": "Tên vật tư",
            "ma_lo": "Mã lô",
            "ma_kho": "Kho",
            "hsd": "Hạn sử dụng",
            "hsd_con_lai": "Số ngày còn lại",
            "canh_bao": "Trạng thái",
            "ton_vi_tri": "SL Tồn",
            "dvt": "ĐVT"
        },
        "summary_fields": ["ton_vi_tri"]
    },

    "inbctuoithotheolo": {
        "id": "inbctuoithotheolo",
        "domain": "KHO",
        "procedure_name": "inbctuoithotheolo",
        "title": "Báo cáo tuổi hàng tồn kho theo lô",
        "aliases": [
            "tuoi hang", "tuoi tho hang", "hang ton bao lau", "tuoi hang theo lo",
            "luu kho bao lau", "hang ton lau"
        ],
        "description": "Theo dõi thời gian lưu kho và số ngày tuổi của từng lô vật tư trong kho.",
        "default_params": {
            "cma_kho": "",
            "cma_vt": "",
            "cma_dvcs": "001",
            "limit": 50,
            "offset": 0,
            "culture": "vi-VN"
        },
        "column_labels": {
            "ma_vt": "Mã vật tư",
            "ten_vt": "Tên vật tư",
            "ma_lo": "Mã lô",
            "ma_kho": "Kho",
            "ngay_nhap": "Ngày nhập",
            "so_ngay_ton": "Số ngày tồn",
            "so_luong": "SL Tồn",
            "dvt": "ĐVT"
        },
        "summary_fields": ["so_luong"]
    },

    "inbctonkhotheosokhuon": {
        "id": "inbctonkhotheosokhuon",
        "domain": "KHO",
        "procedure_name": "inbctonkhotheosokhuon",
        "title": "Báo cáo tồn kho theo số khuôn / Die No",
        "aliases": [
            "ton theo khuon", "ton kho theo khuon", "ton die no", "ton kho theo die",
            "khuon nao con ton", "ton thanh pham theo khuon"
        ],
        "description": "Số lượng tồn kho chi tiết được ép bởi từng mã khuôn hoặc die cụ thể.",
        "default_params": {
            "cma_kho": "",
            "cma_vt": "",
            "cma_dvcs": "001",
            "limit": 50,
            "offset": 0,
            "culture": "vi-VN"
        },
        "column_labels": {
            "ma_vt": "Mã vật tư",
            "ten_vt": "Tên vật tư",
            "ma_khuon": "Mã khuôn / Die",
            "ma_kho": "Kho",
            "so_luong": "SL Tồn",
            "dvt": "ĐVT"
        },
        "summary_fields": ["so_luong"]
    },

    "inbkkiemke": {
        "id": "inbkkiemke",
        "domain": "KHO",
        "procedure_name": "inbkkiemke",
        "title": "Bảng kê phiếu kiểm kê kho",
        "aliases": [
            "kiem ke", "bang ke kiem ke", "phieu kiem ke", "chenh lech kiem ke",
            "kiem ke kho", "so lieu kiem ke"
        ],
        "description": "Bảng kê các đợt kiểm kê kho, đối chiếu số lượng sổ sách và thực tế kiểm kê.",
        "default_params": {
            "cso_ct1": "", "cso_ct2": "",
            "cma_kho": "", "cma_vt": "",
            "cma_dvcs": "001", "limit": 50, "offset": 0, "index": 0,
            "culture": "vi-VN"
        },
        "column_labels": {
            "so_ct": "Số phiếu KK",
            "ngay_ct": "Ngày kiểm kê",
            "ma_kho": "Kho",
            "ma_vt": "Mã VT",
            "ten_vt": "Tên vật tư",
            "sl_so_sach": "SL Sổ sách",
            "sl_thuc_te": "SL Thực tế",
            "sl_chenh_lech": "Chênh lệch",
            "dvt": "ĐVT"
        },
        "summary_fields": ["sl_so_sach", "sl_thuc_te", "sl_chenh_lech"]
    },

    # -------------------------------------------------------------
    # 2. BÁN HÀNG (SALES - SO)
    # -------------------------------------------------------------
    "sobkdonhang": {
        "id": "sobkdonhang",
        "domain": "BAN_HANG",
        "procedure_name": "sobkdonhang",
        "title": "Bảng kê đơn hàng bán (SO)",
        "aliases": [
            "don hang ban", "don ban", "so", "sales order", "bang ke don ban",
            "danh sach don ban", "tinh hinh ban hang", "doanh so ban"
        ],
        "description": "Danh sách đơn đặt hàng bán từ khách hàng, số lượng đặt, đơn giá và trạng thái.",
        "default_params": {
            "cso_ct1": "", "cso_ct2": "",
            "cma_kh": "", "cma_kho": "", "cma_vt": "",
            "cnh_vt1": "", "cnh_vt2": "", "cnh_vt3": "", "cnh_vt4": "", "cnh_vt5": "",
            "cma_nvbh": "", "cma_dvcs": "001",
            "cgiaodich": "", "cstatus": "", "cgroup_yn": "0",
            "limit": 50, "offset": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "so_ct": "Số đơn hàng",
            "ngay_ct": "Ngày đặt",
            "ma_kh": "Mã KH",
            "ten_kh": "Khách hàng",
            "ma_vt": "Mã SP",
            "ten_vt": "Tên sản phẩm",
            "dvt": "ĐVT",
            "so_luong": "SL Đặt",
            "gia": "Đơn giá",
            "tien": "Thành tiền (VND)",
            "thue": "Thuế VAT",
            "statusname": "Trạng thái"
        },
        "summary_fields": ["so_luong", "tien", "thue"]
    },

    "sobctiendogh": {
        "id": "sobctiendogh",
        "domain": "BAN_HANG",
        "procedure_name": "sobctiendogh",
        "title": "Báo cáo tiến độ giao hàng bán",
        "aliases": [
            "tien do giao hang", "giao hang", "da giao bao nhieu", "giao du chua",
            "giao dung han", "tre han", "con no don hang", "ke hoach giao hang"
        ],
        "description": "Theo dõi tiến độ giao hàng: số lượng đặt, đã giao, còn lại, tỷ lệ đúng hạn và trễ hạn.",
        "default_params": {
            "cso_ct1": "", "cso_ct2": "",
            "cma_kh": "", "cma_kho": "", "cma_vt": "",
            "cnh_vt1": "", "cnh_vt2": "", "cnh_vt3": "", "cnh_vt4": "", "cnh_vt5": "",
            "cloai_vt": "", "ctk_vt": "", "ctk_dt": "", "cma_vv": "",
            "cma_dvcs": "001", "limit": 50, "offset": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "so_ct": "Số đơn hàng",
            "ngay_ct": "Ngày đặt",
            "ma_kh": "Mã KH",
            "ten_kh": "Khách hàng",
            "ma_vt": "Mã SP",
            "ten_vt": "Tên sản phẩm",
            "sl_dat": "SL Đặt",
            "sl_da_giao": "Đã giao",
            "sl_con_lai": "Còn lại",
            "ngay_gh": "Ngày GH dự kiến",
            "statusname": "Trạng thái"
        },
        "summary_fields": ["sl_dat", "sl_da_giao", "sl_con_lai"]
    },

    "sobclsgia": {
        "id": "sobclsgia",
        "domain": "BAN_HANG",
        "procedure_name": "sobclsgia",
        "title": "Báo cáo lịch sử thay đổi giá bán",
        "aliases": [
            "gia ban", "bang gia ban", "don gia ban", "lich su gia ban",
            "thay doi gia ban", "gia cho khach", "gia san pham"
        ],
        "description": "Tra cứu giá bán và lịch sử điều chỉnh giá bán của sản phẩm theo khách hàng.",
        "default_params": {
            "cma_kh": "", "cma_vt": "", "culture": "vi-VN"
        },
        "column_labels": {
            "ma_vt": "Mã SP",
            "ten_vt": "Tên sản phẩm",
            "ma_kh": "Mã KH",
            "ngay_bd": "Ngày hiệu lực",
            "gia": "Đơn giá bán",
            "ma_nt": "Tiền tệ",
            "dvt": "ĐVT"
        },
        "summary_fields": []
    },

    "sobklenhgiaohang": {
        "id": "sobklenhgiaohang",
        "domain": "BAN_HANG",
        "procedure_name": None,  # Handled via lookup_delivery_orders in native_tools
        "title": "Bảng kê lệnh giao hàng (TO2) & Out kho",
        "aliases": [
            "lenh giao hang", "lenh to2", "out kho", "hoan thanh out hang",
            "tinh trang lenh giao", "xuat kho to2", "chi thi lo"
        ],
        "description": "Tra cứu chi tiết lệnh giao hàng TO2, số lượng, tình trạng và thời điểm thủ kho out hàng ra khỏi hệ thống.",
        "column_labels": {
            "so_ct": "Số lệnh",
            "ngay_ct": "Ngày lập",
            "ma_kh": "Mã KH",
            "ten_kh": "Khách hàng",
            "ma_vt": "Mã SP",
            "ten_vt": "Tên sản phẩm",
            "so_luong": "Số lượng",
            "ten_trang_thai": "Trạng thái",
            "ngay_hoan_thanh": "Ngày out kho",
            "gio_hoan_thanh": "Giờ out kho",
            "nguoi_hoan_thanh": "Người out kho"
        },
        "summary_fields": ["so_luong"]
    },

    "sobkcthangtralai": {
        "id": "sobkcthangtralai",
        "domain": "BAN_HANG",
        "procedure_name": "sobkcthangtralai",
        "title": "Bảng kê chi tiết hàng bán bị trả lại / Đổi trả NG (HDF)",
        "aliases": [
            "hang tra lai", "hang ban bi tra lai", "hdf", "ng nhan ve",
            "nhan lai hang loi", "khach tra hang", "tra lai ng"
        ],
        "description": "Bảng kê chi tiết các lô hàng khách hàng trả về nhà máy do lỗi NG hoặc đổi trả.",
        "default_params": {
            "cso_ct1": "", "cso_ct2": "",
            "cma_kh": "", "cma_vt": "", "cma_dvcs": "001",
            "limit": 50, "offset": 0, "index": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "so_ct": "Số chứng từ",
            "ngay_ct": "Ngày trả",
            "ma_kh": "Mã KH",
            "ten_kh": "Khách hàng",
            "ma_vt": "Mã SP",
            "ten_vt": "Tên sản phẩm",
            "so_luong": "SL Trả lại",
            "tien": "Giá trị",
            "dien_giai": "Lý do trả lại"
        },
        "summary_fields": ["so_luong", "tien"]
    },

    "sobcthkehoachbh": {
        "id": "sobcthkehoachbh",
        "domain": "BAN_HANG",
        "procedure_name": "sobcthkehoachbh",
        "title": "Báo cáo tình hình thực hiện kế hoạch bán hàng",
        "aliases": [
            "ke hoach ban hang", "thuc hien ke hoach bh", "tien do doanh so",
            "ke hoach vs thuc te bh", "target ban hang"
        ],
        "description": "Đối chiếu doanh số và sản lượng bán hàng thực tế so với chỉ tiêu kế hoạch.",
        "default_params": {
            "cma_nvbh": "", "cma_kh": "", "cma_vt": "", "cma_dvcs": "001",
            "limit": 50, "offset": 0, "index": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "ma_kh": "Mã KH",
            "ten_kh": "Khách hàng",
            "ke_hoach": "Kế hoạch",
            "thuc_hien": "Thực hiện",
            "ty_le": "Tỷ lệ (%)"
        },
        "summary_fields": ["ke_hoach", "thuc_hien"]
    },

    # -------------------------------------------------------------
    # 3. MUA HÀNG (PURCHASING - PO)
    # -------------------------------------------------------------
    "pobkdonhang": {
        "id": "pobkdonhang",
        "domain": "MUA_HANG",
        "procedure_name": "pobkdonhang",
        "title": "Bảng kê đơn đặt mua hàng (PO)",
        "aliases": [
            "don hang mua", "don mua", "po", "purchase order", "bang ke don mua",
            "dat mua ncc", "mua hang ncc", "danh sach don mua"
        ],
        "description": "Bảng kê các đơn đặt mua nguyên vật liệu, phụ tùng từ nhà cung cấp.",
        "default_params": {
            "cso_ct1": "", "cso_ct2": "",
            "cma_kh": "", "cma_vt": "",
            "cnh_vt1": "", "cnh_vt2": "", "cnh_vt3": "", "cnh_vt4": "", "cnh_vt5": "", "cnh_vt6": "", "cnh_vt7": "",
            "cma_dvcs": "001", "cstatus": "", "cgroup_yn": "0",
            "limit": 50, "offset": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "so_ct": "Số PO",
            "ngay_ct": "Ngày đặt",
            "ma_kh": "Mã NCC",
            "ten_kh": "Nhà cung cấp",
            "ma_vt": "Mã vật tư",
            "ten_vt": "Tên vật tư",
            "dvt": "ĐVT",
            "so_luong": "SL Đặt",
            "gia": "Đơn giá mua",
            "tien": "Thành tiền",
            "statusname": "Trạng thái"
        },
        "summary_fields": ["so_luong", "tien"]
    },

    "pobclsgia": {
        "id": "pobclsgia",
        "domain": "MUA_HANG",
        "procedure_name": "pobclsgia",
        "title": "Báo cáo lịch sử thay đổi giá mua NCC",
        "aliases": [
            "gia mua", "gia ncc", "lich su gia mua", "thay doi gia mua",
            "gia vat tu", "gia nhap vao", "gia mua nha cung cap"
        ],
        "description": "Lịch sử biến động đơn giá mua nguyên vật liệu từ các nhà cung cấp.",
        "default_params": {
            "cma_kh": "", "cma_vt": "", "culture": "vi-VN"
        },
        "column_labels": {
            "ma_vt": "Mã vật tư",
            "ten_vt": "Tên vật tư",
            "ma_kh": "Mã NCC",
            "ten_kh": "Nhà cung cấp",
            "ngay_bd": "Ngày hiệu lực",
            "gia": "Đơn giá mua",
            "dvt": "ĐVT",
            "ma_nt": "Tiền tệ"
        },
        "summary_fields": []
    },

    "postatus": {
        "id": "postatus",
        "domain": "MUA_HANG",
        "procedure_name": "postatus",
        "title": "Báo cáo tình trạng đơn hàng mua (PO Status)",
        "aliases": [
            "tinh trang don mua", "po status", "ncc da giao chua", "tien do don mua",
            "hang mua ve chua", "don mua con no"
        ],
        "description": "Theo dõi tình trạng đơn đặt mua: số lượng đặt, số lượng NCC đã giao, số lượng còn nợ lại.",
        "default_params": {
            "cso_ct1": "", "cso_ct2": "",
            "cma_kh": "", "cma_kho": "", "cma_vt": "",
            "cma_dvcs": "001", "time_from": "00:00", "time_to": "23:59",
            "limit": 50, "offset": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "so_ct": "Số PO",
            "ngay_ct": "Ngày đặt",
            "ma_kh": "Mã NCC",
            "ten_kh": "Nhà cung cấp",
            "ma_vt": "Mã vật tư",
            "ten_vt": "Tên vật tư",
            "sl_dat": "SL Đặt",
            "sl_nhap": "Đã nhập",
            "sl_con_lai": "Còn lại",
            "statusname": "Trạng thái"
        },
        "summary_fields": ["sl_dat", "sl_nhap", "sl_con_lai"]
    },

    "pobkhoadon": {
        "id": "pobkhoadon",
        "domain": "MUA_HANG",
        "procedure_name": "pobkhoadon",
        "title": "Bảng kê hóa đơn mua hàng",
        "aliases": [
            "hoa don mua", "hoa don ncc", "bang ke hoa don mua", "pobkhoadon", "chung tu mua hang"
        ],
        "description": "Bảng kê hóa đơn GTGT / hóa đơn mua hàng từ các nhà cung cấp.",
        "default_params": {
            "cso_ct1": "", "cso_ct2": "",
            "cma_kh": "", "cma_vt": "", "cma_dvcs": "001",
            "limit": 50, "offset": 0, "index": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "so_ct": "Số HĐ",
            "ngay_ct": "Ngày HĐ",
            "ma_kh": "Mã NCC",
            "ten_kh": "Nhà cung cấp",
            "tien": "Tiền hàng",
            "thue": "Thuế VAT",
            "tong_tien": "Tổng thanh toán"
        },
        "summary_fields": ["tien", "thue", "tong_tien"]
    },

    "pobknhap": {
        "id": "pobknhap",
        "domain": "MUA_HANG",
        "procedure_name": "pobknhap",
        "title": "Bảng kê phiếu nhập mua hàng (PND / PR1)",
        "aliases": [
            "phieu nhap mua", "nhap hang mua", "bang ke nhap mua", "nhap kho nvl ncc",
            "pobknhap", "nhap mua hang"
        ],
        "description": "Bảng kê các phiếu nhập kho thực tế đối với vật tư, phụ tùng mua từ NCC.",
        "default_params": {
            "cso_ct1": "", "cso_ct2": "",
            "cma_kh": "", "cma_kho": "", "cma_vt": "", "cma_dvcs": "001",
            "time_from": "00:00", "time_to": "23:59",
            "limit": 50, "offset": 0, "index": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "so_ct": "Số phiếu nhập",
            "ngay_ct": "Ngày nhập",
            "ma_kh": "Mã NCC",
            "ten_kh": "Nhà cung cấp",
            "ma_vt": "Mã VT",
            "ten_vt": "Tên vật tư",
            "so_luong": "SL Nhập",
            "gia": "Đơn giá",
            "tien": "Thành tiền"
        },
        "summary_fields": ["so_luong", "tien"]
    },

    "pobkxuattra": {
        "id": "pobkxuattra",
        "domain": "MUA_HANG",
        "procedure_name": "pobkxuattra",
        "title": "Bảng kê phiếu xuất trả lại nhà cung cấp (PXC)",
        "aliases": [
            "xuat tra ncc", "tra lai ncc", "tra hang ncc", "phieu xuat tra",
            "pxc", "xuat tra nha cung cap"
        ],
        "description": "Bảng kê các lần xuất kho trả lại vật tư kém chất lượng cho nhà cung cấp.",
        "default_params": {
            "cso_ct1": "", "cso_ct2": "",
            "cma_kh": "", "cma_vt": "", "cma_dvcs": "001",
            "limit": 50, "offset": 0, "index": 0, "culture": "vi-VN"
        },
        "column_labels": {
            "so_ct": "Số phiếu xuất",
            "ngay_ct": "Ngày xuất",
            "ma_kh": "Mã NCC",
            "ten_kh": "Nhà cung cấp",
            "ma_vt": "Mã VT",
            "ten_vt": "Tên vật tư",
            "so_luong": "SL Xuất trả",
            "tien": "Giá trị"
        },
        "summary_fields": ["so_luong", "tien"]
    },

    # -------------------------------------------------------------
    # 4. CÔNG NỢ & KẾ TOÁN (AR / AP - DEBT)
    # -------------------------------------------------------------
    "sosoctcongno1kh": {
        "id": "sosoctcongno1kh",
        "domain": "CONG_NO",
        "procedure_name": "sosoctcongno1kh",
        "title": "Sổ chi tiết công nợ đối tác (TK 131 / 331)",
        "aliases": [
            "cong no", "so chi tiet cong no", "no phai thu", "no phai tra",
            "du no", "so du cong no", "khach no bao nhieu", "no ncc", "tk 131", "tk 331"
        ],
        "description": "Sổ chi tiết phát sinh và số dư công nợ của một khách hàng (TK 131) hoặc nhà cung cấp (TK 331).",
        "default_params": {
            "caccount": "131",
            "ccust": "",
            "cbranch": "001",
            "isdetail": 1,
            "cculture": "vi-VN"
        },
        "column_labels": {
            "ngay_ct": "Ngày CT",
            "so_ct": "Số chứng từ",
            "dien_giai": "Diễn giải",
            "ps_no": "Phát sinh Nợ",
            "ps_co": "Phát sinh Có",
            "du_no": "Dư Nợ",
            "du_co": "Dư Có"
        },
        "summary_fields": ["ps_no", "ps_co"]
    },

    "posoctcongno1ncc": {
        "id": "posoctcongno1ncc",
        "domain": "CONG_NO",
        "procedure_name": "posoctcongno1ncc",
        "title": "Sổ chi tiết công nợ nhà cung cấp (TK 331)",
        "aliases": [
            "cong no ncc", "so chi tiet cong no ncc", "no ncc bao nhieu", "phai tra ncc",
            "cong no 331", "so du 331", "cong no nha cung cap"
        ],
        "description": "Sổ chi tiết công nợ phải trả cho nhà cung cấp theo tài khoản 331.",
        "default_params": {
            "caccount": "331",
            "ccust": "",
            "cbranch": "001",
            "isdetail": 1,
            "cculture": "vi-VN"
        },
        "column_labels": {
            "ngay_ct": "Ngày CT",
            "so_ct": "Số chứng từ",
            "dien_giai": "Diễn giải",
            "ps_no": "Phát sinh Nợ (Đã trả)",
            "ps_co": "Phát sinh Có (Mua chịu)",
            "du_no": "Dư Nợ",
            "du_co": "Dư Có (Còn phải trả)"
        },
        "summary_fields": ["ps_no", "ps_co"]
    },

    # -------------------------------------------------------------
    # 5. CHẤT LƯỢNG (QUALITY - QC)
    # -------------------------------------------------------------
    "lookup_incoming_quality": {
        "id": "lookup_incoming_quality",
        "domain": "CHAT_LUONG",
        "procedure_name": None,  # Handled via direct phiqc query
        "title": "Báo cáo chất lượng hàng mua đầu vào (IQC)",
        "aliases": [
            "chat luong", "iqc", "chat luong hang mua", "danh gia ncc",
            "ty le dat", "so lo ng", "so lo dat", "loi ncc", "kiem tra nvl"
        ],
        "description": "Đánh giá chất lượng hàng mua vào theo nhà cung cấp: tổng lô nhập, số lô đạt, số lô NG và tỷ lệ đạt (%).",
        "column_labels": {
            "ma_ncc": "Mã NCC",
            "ten_ncc": "Tên nhà cung cấp",
            "tong_so_lo": "Tổng số lô kiểm",
            "so_lo_dat": "Số lô Đạt",
            "so_lo_ng": "Số lô NG",
            "ty_le_dat_lo": "Tỷ lệ Đạt (%)",
            "tong_so_luong_nhap": "Tổng SL nhập"
        },
        "summary_fields": ["tong_so_lo", "so_lo_dat", "so_lo_ng", "tong_so_luong_nhap"]
    },

    "lookup_qc_lot_status": {
        "id": "lookup_qc_lot_status",
        "domain": "CHAT_LUONG",
        "procedure_name": None,  # Handled via intem_log status_qc
        "title": "Kiểm tra trạng thái QC tem thành phẩm (OK / NG / Khóa)",
        "aliases": [
            "trang thai qc", "status qc", "khoanh vung ng", "khoa lot",
            "tem bi khoa", "lot bi khoa", "lo bi ng", "chat luong tem"
        ],
        "description": "Kiểm tra tem thành phẩm hiện hành có lot nào đang ở trạng thái khóa (5-NG) hoặc chờ xử lý (6) không.",
        "column_labels": {
            "form_name": "Trạng thái QC",
            "qty": "Số lượng (PCS)",
            "count_tem": "Số lượng tem"
        },
        "summary_fields": ["qty", "count_tem"]
    },

    "lookup_mes_ng": {
        "id": "lookup_mes_ng",
        "domain": "CHAT_LUONG",
        "procedure_name": None,  # Handled via mes_oi_ng_confirm in native_tools
        "title": "Báo cáo xác nhận phế phẩm / lỗi sản xuất NG (MES)",
        "aliases": [
            "phe pham", "loi ng", "loi san xuat", "ng san xuat", "hang loi",
            "xac nhan ng", "ng theo may", "phe pham theo may"
        ],
        "description": "Báo cáo tổng hợp số lượng sản phẩm phế phẩm NG theo máy, theo công đoạn và nguyên nhân lỗi.",
        "column_labels": {
            "ngay_phat_sinh": "Ngày",
            "ma_may": "Mã máy",
            "ma_sp": "Mã SP",
            "ten_sp": "Tên sản phẩm",
            "cong_doan": "Công đoạn",
            "sl_ng": "SL Lỗi NG",
            "so_lan_ng": "Số lần",
            "ghi_chu": "Ghi chú lỗi"
        },
        "summary_fields": ["sl_ng", "so_lan_ng"]
    },

    # -------------------------------------------------------------
    # 6. SẢN XUẤT & MES (MANUFACTURING / MES)
    # -------------------------------------------------------------
    "mesbkwo": {
        "id": "mesbkwo",
        "domain": "SAN_XUAT",
        "procedure_name": "mesbkwo",
        "title": "Bảng kê điều độ sản xuất & Work Order (Lệnh SX)",
        "aliases": [
            "dieu do san xuat", "work order", "wo", "lenh san xuat", "ke hoach san xuat",
            "dieu do", "danh sach wo", "wo dang chay", "lich san xuat"
        ],
        "description": "Bảng kê các Work Order đang điều độ sản xuất: mã máy, mã khuôn, số lượng kế hoạch, thời gian chạy và tiến độ.",
        "default_params": {
            "cma_day_chuyen": "", "cmes_scheduling_code": "", "cma_vt": "",
            "cproduction_order": "", "cma_dvcs": "001", "mau_bc": "",
            "limit": 50, "offset": 0
        },
        "column_labels": {
            "machine_code": "Mã máy",
            "product_code": "Mã SP",
            "ten_vt": "Tên sản phẩm",
            "mold_code": "Mã khuôn",
            "mes_scheduling_code": "Mã W/O",
            "quantity": "SL Kế hoạch",
            "start_date": "Ngày bắt đầu",
            "end_date": "Ngày kết thúc",
            "statusname": "Trạng thái",
            "production_order": "Lệnh SX"
        },
        "summary_fields": ["quantity"]
    },

    "mesbkdongthung": {
        "id": "mesbkdongthung",
        "domain": "SAN_XUAT",
        "procedure_name": None,  # Handled via lookup_mes_packing
        "title": "Bảng kê đóng thùng thành phẩm MES",
        "aliases": [
            "dong thung", "dong goi", "serial tem thung", "thung thanh pham",
            "dong thung mes", "bang ke dong thung"
        ],
        "description": "Bảng kê các thùng thành phẩm đã được quét đóng gói tại các trạm máy sản xuất.",
        "column_labels": {
            "serial_tem_thung": "Serial thùng",
            "product_code": "Mã sản phẩm",
            "product_name": "Tên sản phẩm",
            "quantity": "Số lượng/Thùng",
            "station_code": "Trạm máy",
            "production_order": "Lệnh SX",
            "mes_scheduling_code": "Số W/O"
        },
        "summary_fields": ["quantity"]
    },

    "mesbkgoptachthung": {
        "id": "mesbkgoptachthung",
        "domain": "SAN_XUAT",
        "procedure_name": "mesbkgoptachthung",
        "title": "Bảng kê gộp tách thùng tem carton MES",
        "aliases": [
            "gop tach thung", "gop thung", "tach thung", "chia thung", "chuyen thung",
            "doi thung", "lich su tach thung"
        ],
        "description": "Theo dõi lịch sử các thao tác gộp thùng hoặc tách lẻ thùng tem carton tại xưởng.",
        "default_params": {
            "cma_day_chuyen": "", "cma_vt": "", "cma_dvcs": "001",
            "cgroup_yn": "1", "mau_bc": "001", "limit": 50, "offset": 0
        },
        "column_labels": {
            "ngay_ghi_nhan": "Ngày thao tác",
            "production_order": "Lệnh SX",
            "product_code": "Mã sản phẩm",
            "so_luong": "Số lượng",
            "dien_giai": "Diễn giải"
        },
        "summary_fields": ["so_luong"]
    },

    "mesbkbosungshot": {
        "id": "mesbkbosungshot",
        "domain": "SAN_XUAT",
        "procedure_name": "mesbkbosungshot",
        "title": "Bảng kê bổ sung hoặc bỏ shot khuôn trong ca sản xuất",
        "aliases": [
            "bo sung hoac bo shot", "bo sung shot", "bo shot", "shot bo sung", "shot huy",
            "dieu chinh shot", "tang giam shot", "shot bat thuong", "bo sung shot khuon", "bo shot khuon"
        ],
        "description": "Nhật ký các lần kỹ thuật viên hoặc máy bổ sung thêm shot hoặc loại bỏ shot hỏng trong ca làm việc.",
        "default_params": {
            "cma_dvcs": "001", "cgroup_yn": "1", "mau_bc": "001", "limit": 50, "offset": 0
        },
        "column_labels": {
            "line_code": "Dây chuyền / Máy",
            "mes_scheduling_code": "Số W/O",
            "date0": "Ngày ghi nhận",
            "shot_count": "Số shot điều chỉnh",
            "ly_do": "Lý do"
        },
        "summary_fields": []
    },

    "mesbkthaykhuon": {
        "id": "mesbkthaykhuon",
        "domain": "SAN_XUAT",
        "procedure_name": "mesbkthaykhuon",
        "title": "Lịch sử các lần thay khuôn sản xuất MES",
        "aliases": [
            "thay khuon", "lich su thay khuon", "doi khuon", "lap khuon",
            "ha khuon", "thoi gian thay khuon"
        ],
        "description": "Nhật ký hạ khuôn, gá lắp khuôn mới và thời gian setup khuôn trên các máy ép.",
        "default_params": {
            "cma_dvcs": "001", "cgroup_yn": "1", "mau_bc": "001", "limit": 50, "offset": 0
        },
        "column_labels": {
            "so_ct": "Số chứng từ",
            "ngay_ct": "Ngày thay",
            "so_wo": "Số W/O",
            "ma_vt": "Mã sản phẩm",
            "ma_khuon": "Mã khuôn",
            "ma_may": "Mã máy",
            "thoi_gian_setup": "Thời gian setup (phút)"
        },
        "summary_fields": []
    },

    "lookup_mold_and_mes": {
        "id": "lookup_mold_and_mes",
        "domain": "SAN_XUAT",
        "procedure_name": None,  # Handled via mes_mold_shot_current / dmmold
        "title": "Hồ sơ khuôn mẫu & Số shot dập thực tế",
        "aliases": [
            "khuon", "so shot", "shot khuon", "tuoi tho khuon", "dap bao nhieu shot",
            "dinh muc bao hanh", "tinh trang khuon"
        ],
        "description": "Số shot đã dập thực tế, định mức bảo hành và thông tin hồ sơ khuôn ép nhựa.",
        "column_labels": {
            "mold_code": "Mã khuôn",
            "mold_name": "Tên khuôn",
            "total_shot": "Tổng shot dập",
            "guarantee_shots": "Định mức bảo hành",
            "cavity_count": "Số cavity",
            "part_code": "Mã sản phẩm",
            "status": "Trạng thái"
        },
        "summary_fields": ["total_shot"]
    },

    "lookup_bom": {
        "id": "lookup_bom",
        "domain": "SAN_XUAT",
        "procedure_name": None,  # Handled via mes_bom / dmvt
        "title": "Cấu trúc định mức sản phẩm (BOM)",
        "aliases": [
            "bom", "dinh muc", "cau truc san pham", "dung hat nhua gi",
            "nguyen lieu san pham", "tieu hao", "ti le nvl"
        ],
        "description": "BOM sản phẩm: loại hạt nhựa / linh kiện cấu thành, định mức tiêu hao, đơn vị và ngày hiệu lực.",
        "column_labels": {
            "product_code": "Mã sản phẩm",
            "product_name": "Tên sản phẩm",
            "material_code": "Mã nguyên liệu",
            "material_name": "Tên nguyên liệu",
            "dinh_muc": "Định mức",
            "uom": "ĐVT",
            "bom_version": "Version",
            "valid_from": "Hiệu lực từ"
        },
        "summary_fields": []
    },

    "lookup_mes_downtime": {
        "id": "lookup_mes_downtime",
        "domain": "SAN_XUAT",
        "procedure_name": None,  # Handled via mes_machine_stop / mes_stop_code
        "title": "Báo cáo thời gian dừng máy (Downtime) theo nguyên nhân",
        "aliases": [
            "dung may", "thoi gian dung", "ngung may", "downtime", "stop line",
            "nguyen nhan dung may", "may hong", "dung san xuat"
        ],
        "description": "Tổng hợp thời gian dừng máy (phút), số lần dừng theo nguyên nhân sự cố trong khoảng thời gian.",
        "column_labels": {
            "nguyen_nhan": "Nguyên nhân dừng",
            "so_lan_dung": "Số lần dừng",
            "tong_phut_dung": "Tổng phút dừng"
        },
        "summary_fields": ["so_lan_dung", "tong_phut_dung"]
    },

    "bctdecn": {
        "id": "bctdecn",
        "domain": "SAN_XUAT",
        "procedure_name": "bctdecn",
        "title": "Báo cáo theo dõi tiến độ ECN (Thay đổi kỹ thuật)",
        "aliases": [
            "ecn", "thay doi ky thuat", "tien do ecn", "theo doi ecn",
            "lenh ecn", "cai tien san pham"
        ],
        "description": "Báo cáo tiến độ triển khai các yêu cầu thay đổi kỹ thuật, khuôn và vật tư (ECN).",
        "default_params": {
            "cma_kh": "", "cma_vt": "", "cma_dvcs": "001",
            "cgroup_yn": "1", "mau_bc": "001", "limit": 50, "offset": 0
        },
        "column_labels": {
            "so_ct": "Số ECN",
            "ngay_ct": "Ngày lập",
            "ma_kh": "Mã KH",
            "ma_vt": "Mã sản phẩm",
            "noi_dung": "Nội dung thay đổi",
            "trang_thai": "Tiến độ"
        },
        "summary_fields": []
    },

    "bctdnmd": {
        "id": "bctdnmd",
        "domain": "SAN_XUAT",
        "procedure_name": "bctdnmd",
        "title": "Báo cáo theo dõi tiến độ giao mẫu sản phẩm mới (NMD)",
        "aliases": [
            "nmd", "giao mau", "tien do nmd", "mau moi", "giao mau khach hang"
        ],
        "description": "Theo dõi tiến độ chế thử và giao mẫu sản phẩm mới cho khách hàng.",
        "default_params": {
            "cma_kh": "", "cma_vt": "", "cma_dvcs": "001",
            "cgroup_yn": "1", "mau_bc": "001", "limit": 50, "offset": 0
        },
        "column_labels": {
            "so_ct": "Số phiếu",
            "ngay_ct": "Ngày giao",
            "ma_kh": "Mã KH",
            "ma_vt": "Mã sản phẩm",
            "so_luong": "SL Mẫu",
            "ket_qua": "Kết quả đánh giá"
        },
        "summary_fields": ["so_luong"]
    },

    # -------------------------------------------------------------
    # 7. DANH MỤC & ĐÓNG GÓI (CATALOG & PACKAGING)
    # -------------------------------------------------------------
    "lookup_general_catalog": {
        "id": "lookup_general_catalog",
        "domain": "DANH_MUC",
        "procedure_name": None,  # Handled via dmvt / sys_user
        "title": "Tra cứu danh mục thông tin chung & Quy cách đóng gói",
        "aliases": [
            "quy cach dong goi", "dong goi", "bao bi", "dong thung", "khay",
            "thung bao nhieu", "packs0", "tai khoan hp", "nhan vien", "hp4509", "4509",
            "danh muc", "tim khach hang", "ma khach hang", "ma ncc",
            "khach hang cua ma hang", "ma hang thuoc khach hang nao", "khach hang so huu",
            "ma vat tu thuoc khach hang", "khai bao thuoc khach hang", "tra cuu ma hang",
            "thong tin ma hang", "khach hang cua san pham"
        ],
        "description": "Quy cách đóng gói vật tư (số lượng/thùng, khay), tra cứu mã hàng thuộc khách hàng nào, hoặc mã nhân viên, khách hàng, nhà cung cấp.",
        "column_labels": {
            "ma_vt": "Mã vật tư",
            "ten_vt": "Tên vật tư",
            "dvt": "ĐVT",
            "model": "Model",
            "ma_kh": "Mã khách hàng",
            "ten_kh": "Tên khách hàng",
            "dia_chi": "Địa chỉ khách hàng",
            "so_luong_thung": "SL/Thùng",
            "so_luong_khay": "SL/Khay",
            "ma_thung": "Mã thùng",
            "ma_khay": "Mã khay"
        },
        "summary_fields": []
    },


    "inbckstonkholo": {       'aliases': ['ton kho lo', 'ton lo chua chi thi', 'kiem soat lo ton', 'ton theo lo', 'inbckstonkholo'],
        'column_labels': {       'dvt': 'ĐVT',
                                 'ma_kho': 'Mã kho',
                                 'ma_lo': 'Mã lô',
                                 'ma_vt': 'Mã vật tư',
                                 'ten_vt': 'Tên vật tư',
                                 'ton_cuoi': 'Tồn cuối kỳ'},
        'default_params': {       'cgroup_yn': '0',
                                  'cma_dvcs': '001',
                                  'cma_kho': '',
                                  'cma_vt': '',
                                  'cstatus': '*',
                                  'culture': 'vi-VN',
                                  'dfrom': '',
                                  'dto': '',
                                  'limit': 50,
                                  'mau_bc': '001',
                                  'offset': 0},
        'description': 'Kiểm soát chi tiết tồn kho theo từng số lô nhập, ngày hết hạn và số lượng khả dụng.',
        'domain': 'KHO',
        'id': 'inbckstonkholo',
        'procedure_name': 'inbckstonkholo',
        'summary_fields': ['ton_cuoi'],
        'title': 'Báo cáo kiểm soát tồn kho theo lô'},

    "inbctrangthaikho": {       'aliases': ['trang thai kho', 'suc chua kho', 'vi tri trong', 'vi tri kho trong', 'tinh trang vi tri'],
        'column_labels': {       'ma_kho': 'Mã kho',
                                 'ma_vi_tri': 'Vị trí / Kệ',
                                 'ma_vt': 'Mã vật tư',
                                 'so_luong': 'Tồn vị trí',
                                 'suc_chua': 'Sức chứa tối đa',
                                 'ten_kho': 'Tên kho'},
        'default_params': {},
        'description': 'Tra cứu tổng hợp tình trạng sức chứa, số vị trí còn trống và phân bổ kệ/vị trí của từng kho.',
        'domain': 'KHO',
        'id': 'inbctrangthaikho',
        'procedure_name': None,
        'summary_fields': ['so_luong'],
        'title': 'Báo cáo trạng thái kho và sức chứa vị trí'},

    "dmbanggiact": {       'aliases': ['gia ban', 'bang gia ban', 'chinh sach gia', 'don gia ban', 'gia niem yet', 'gia xuat ban'],
        'column_labels': {       'gia_nt': 'Đơn giá bán',
                                 'ma_kh': 'Mã khách hàng',
                                 'ma_nt': 'Tiền tệ',
                                 'ma_vt': 'Mã sản phẩm',
                                 'ngay_hl': 'Ngày hiệu lực',
                                 'ten_kh': 'Tên khách hàng',
                                 'ten_vt': 'Tên sản phẩm'},
        'default_params': {},
        'description': 'Tra cứu bảng giá bán và chính sách giá theo khách hàng hoặc sản phẩm cụ thể.',
        'domain': 'BAN_HANG',
        'id': 'dmbanggiact',
        'procedure_name': None,
        'summary_fields': [],
        'title': 'Bảng giá bán / Chính sách giá sản phẩm'},

    "sobctonghopbh": {       'aliases': [       'tong hop ban hang',
                           'doanh so ban hang',
                           'doanh thu ban hang',
                           'tong hop doanh so',
                           'sobctonghopbh'],
        'column_labels': {       'ma_kh': 'Mã KH',
                                 'ma_vt': 'Mã SP',
                                 'so_luong': 'SL Bán',
                                 'ten_kh': 'Tên khách hàng',
                                 'ten_vt': 'Tên sản phẩm',
                                 'tien': 'Doanh số (VND)'},
        'default_params': {       'cgroup_yn': '1',
                                  'cma_dvcs': '001',
                                  'cma_kh': '',
                                  'cma_vt': '',
                                  'cstatus': '*',
                                  'culture': 'vi-VN',
                                  'dfrom': '',
                                  'dto': '',
                                  'limit': 50,
                                  'mau_bc': '001',
                                  'offset': 0},
        'description': 'Tổng hợp doanh số, khối lượng xuất bán theo khách hàng, nhóm sản phẩm và khoảng thời gian.',
        'domain': 'BAN_HANG',
        'id': 'sobctonghopbh',
        'procedure_name': 'sobctonghopbh',
        'summary_fields': ['so_luong', 'tien'],
        'title': 'Báo cáo tổng hợp bán hàng (tuần/tháng/doanh số)'},

    "sobkdubaotieuthu": {       'aliases': ['du bao tieu thu', 'du bao ban hang', 'forecast', 'du bao nhu cau', 'sobkdubaotieuthu'],
        'column_labels': {       'ma_fc': 'Mã Forecast',
                                 'ma_kh': 'Mã KH',
                                 'ma_vt': 'Mã SP',
                                 'ngay_nhu_cau': 'Ngày nhu cầu',
                                 'so_luong': 'SL Dự báo'},
        'default_params': {},
        'description': 'Kế hoạch dự báo nhu cầu giao hàng và sản xuất theo tháng từ khách hàng.',
        'domain': 'BAN_HANG',
        'id': 'sobkdubaotieuthu',
        'procedure_name': None,
        'summary_fields': ['so_luong'],
        'title': 'Bảng kê dự báo tiêu thụ (Forecast)'},

    "sobkbaogia": {       'aliases': ['bang ke bao gia', 'bao gia khach hang', 'giay bao gia', 'sobkbaogia'],
        'column_labels': {       'gia': 'Đơn giá chào',
                                 'ma_kh': 'Mã KH',
                                 'ma_vt': 'Mã SP',
                                 'ngay_ct': 'Ngày báo giá',
                                 'so_ct': 'Số báo giá',
                                 'status': 'Trạng thái'},
        'default_params': {},
        'description': 'Lịch sử và danh sách báo giá bán đã gửi cho khách hàng.',
        'domain': 'BAN_HANG',
        'id': 'sobkbaogia',
        'procedure_name': None,
        'summary_fields': [],
        'title': 'Bảng kê giấy báo giá bán hàng'},

    "dmgiamuact": {       'aliases': ['gia mua ncc', 'bang gia mua', 'gia nha cung cap', 'chinh sach gia mua', 'danh muc gia mua'],
        'column_labels': {       'gia': 'Đơn giá mua (VND)',
                                 'ma_ncc': 'Mã NCC',
                                 'ma_nt': 'Tiền tệ',
                                 'ma_vt': 'Mã vật tư',
                                 'ngay_hh': 'Ngày hết hạn',
                                 'ngay_hl': 'Ngày hiệu lực',
                                 'ten_ncc': 'Nhà cung cấp',
                                 'ten_vt': 'Tên vật tư'},
        'default_params': {},
        'description': 'Tra cứu bảng giá mua vật tư, hạt nhựa từ các nhà cung cấp theo thời hạn hiệu lực.',
        'domain': 'MUA_HANG',
        'id': 'dmgiamuact',
        'procedure_name': None,
        'summary_fields': [],
        'title': 'Bảng giá mua nhà cung cấp (NCC)'},

    "pobkycnhap": {       'aliases': ['yeu cau nhap', 'phieu yeu cau nhap', 'pr mua hang', 'pr nhap', 'pobkycnhap'],
        'column_labels': {       'ma_vt': 'Mã VT',
                                 'ngay_ct': 'Ngày yêu cầu',
                                 'ngay_giao': 'Ngày cần hàng',
                                 'so_ct': 'Số PR',
                                 'so_luong': 'SL Yêu cầu',
                                 'ten_vt': 'Tên vật tư'},
        'default_params': {       'cgroup_yn': '0',
                                  'cma_dvcs': '001',
                                  'cma_kh': '',
                                  'cma_vt': '',
                                  'cstatus': '*',
                                  'culture': 'vi-VN',
                                  'dfrom': '',
                                  'dto': '',
                                  'limit': 50,
                                  'mau_bc': '001',
                                  'offset': 0},
        'description': 'Theo dõi các phiếu yêu cầu mua hàng / nhập hàng phát sinh từ phòng ban.',
        'domain': 'MUA_HANG',
        'id': 'pobkycnhap',
        'procedure_name': 'pobkycnhap',
        'summary_fields': ['so_luong'],
        'title': 'Bảng kê phiếu yêu cầu nhập hàng (PR)'},

    "pobkycmua": {       'aliases': ['yeu cau mua', 'phieu yeu cau mua', 'de nghi mua hang', 'pobkycmua'],
        'column_labels': {       'dien_giai': 'Lý do mua',
                                 'ma_vt': 'Mã VT',
                                 'ngay_ct': 'Ngày yêu cầu',
                                 'so_ct': 'Số yêu cầu',
                                 'so_luong': 'SL Mua',
                                 'ten_vt': 'Tên vật tư'},
        'default_params': {       'cgroup_yn': '0',
                                  'cma_dvcs': '001',
                                  'cma_kh': '',
                                  'cma_vt': '',
                                  'cstatus': '*',
                                  'culture': 'vi-VN',
                                  'dfrom': '',
                                  'dto': '',
                                  'limit': 50,
                                  'mau_bc': '001',
                                  'offset': 0},
        'description': 'Danh sách các đề nghị và yêu cầu mua hàng đang chờ phê duyệt hoặc đặt PO.',
        'domain': 'MUA_HANG',
        'id': 'pobkycmua',
        'procedure_name': 'pobkycmua',
        'summary_fields': ['so_luong'],
        'title': 'Bảng kê yêu cầu mua hàng'},

    "pothnhap": {       'aliases': [
                            'tong hop nhap mua', 'tong hop hang nhap mua', 'tong hop hang nhap', 
                            'hang nhap mua', 'tong hop mua hang', 'tong hop hang nhap ncc', 
                            'nhap mua tu nha cung cap', 'th nhap mua', 'pothnhap'
                        ],
        'column_labels': {       'ma_kh': 'Mã NCC',
                                 'ma_vt': 'Mã VT',
                                 'so_luong': 'Tổng SL Nhập',
                                 'ten_kh': 'Nhà cung cấp',
                                 'ten_vt': 'Tên vật tư',
                                 'tien': 'Tổng giá trị (VND)'},
        'default_params': {       'cgroup_yn': '1',
                                  'cma_dvcs': '001',
                                  'cma_kh': '',
                                  'cma_vt': '',
                                  'cstatus': '*',
                                  'culture': 'vi-VN',
                                  'dfrom': '',
                                  'dto': '',
                                  'limit': 50,
                                  'mau_bc': '001',
                                  'offset': 0},
        'description': 'Tổng hợp khối lượng và giá trị nguyên vật liệu đã nhập mua từ các nhà cung cấp.',
        'domain': 'MUA_HANG',
        'id': 'pothnhap',
        'procedure_name': 'pothnhap',
        'summary_fields': ['so_luong', 'tien'],
        'title': 'Báo cáo tổng hợp hàng nhập mua theo NCC & vật tư'},

    "glso1": {       'aliases': [       'so cai',
                           'so cai tai khoan',
                           'so chi tiet tai khoan',
                           'phat sinh tai khoan',
                           'so phat sinh tk',
                           'glso1',
                           'so nhat ky chung'],
        'column_labels': {       'dien_giai': 'Diễn giải',
                                 'ma_kh': 'Mã đối tác',
                                 'ngay_ct': 'Ngày hạch toán',
                                 'ps_co': 'Phát sinh Có (VND)',
                                 'ps_no': 'Phát sinh Nợ (VND)',
                                 'so_ct': 'Số chứng từ',
                                 'tk': 'Tài khoản',
                                 'tk_du': 'TK Đối ứng'},
        'default_params': {},
        'description': 'Sổ cái chi tiết các nghiệp vụ kế toán phát sinh của tài khoản (TK 111, 112, 131, 152, 154, '
                       '155, 331, 511, 621, 641, 642).',
        'domain': 'KE_TOAN',
        'id': 'glso1',
        'procedure_name': None,
        'summary_fields': ['ps_no', 'ps_co'],
        'title': 'Sổ cái tài khoản kế toán / Sổ chi tiết phát sinh theo tài khoản'},

    "glbccdsp": {       'aliases': [       'can doi phat sinh',
                           'bang can doi phat sinh',
                           'can doi so phat sinh',
                           'cdps',
                           'glbccdsp',
                           'bang can doi tai khoan'],
        'column_labels': {       'ten_tk': 'Tên tài khoản',
                                 'tk': 'Số hiệu TK',
                                 'tong_co': 'Tổng phát sinh Có (VND)',
                                 'tong_no': 'Tổng phát sinh Nợ (VND)'},
        'default_params': {},
        'description': 'Bảng tổng hợp cân đối số phát sinh Nợ và Có của toàn bộ hệ thống tài khoản kế toán trong kỳ.',
        'domain': 'KE_TOAN',
        'id': 'glbccdsp',
        'procedure_name': None,
        'summary_fields': ['tong_no', 'tong_co'],
        'title': 'Bảng cân đối số phát sinh các tài khoản (Trial Balance)'},

    "glsoctthuchi": {       'aliases': [       'so quy',
                           'so quy tien mat',
                           'so tien gui',
                           'thu chi',
                           'so nhat ky thu chi',
                           'thu chi tien mat',
                           'glsoctthuchi'],
        'column_labels': {       'chi': 'Số tiền Chi (VND)',
                                 'dien_giai': 'Nội dung thu/chi',
                                 'ngay_ct': 'Ngày chứng từ',
                                 'so_ct': 'Số phiếu',
                                 'thu': 'Số tiền Thu (VND)',
                                 'tk': 'Tài khoản',
                                 'tk_du': 'TK Đối ứng'},
        'default_params': {},
        'description': 'Nhật ký thu chi tiền mặt và dòng tiền gửi ngân hàng theo từng phiếu thu, phiếu chi, giấy báo '
                       'có/báo nợ.',
        'domain': 'KE_TOAN',
        'id': 'glsoctthuchi',
        'procedure_name': None,
        'summary_fields': ['thu', 'chi'],
        'title': 'Sổ quỹ tiền mặt và tiền gửi ngân hàng (TK 111 / 112)'},

    "glbcchiphi": {       'aliases': [       'chi phi san xuat',
                           'chi phi quan ly',
                           'tap hop chi phi',
                           'bao cao chi phi',
                           'chi phi nvl',
                           'chi phi tk 154',
                           'glbcchiphi'],
        'column_labels': {'chi_phi': 'Chi phí tập hợp (VND)', 'ten_tk': 'Tên loại chi phí', 'tk': 'Tài khoản chi phí'},
        'default_params': {},
        'description': 'Báo cáo tập hợp các khoản chi phí sản xuất kinh doanh dở dang, chi phí bán hàng và chi phí '
                       'quản lý.',
        'domain': 'KE_TOAN',
        'id': 'glbcchiphi',
        'procedure_name': None,
        'summary_fields': ['chi_phi'],
        'title': 'Báo cáo tập hợp chi phí sản xuất và quản lý (TK 154 / 621 / 641 / 642)'},

    "mesbcoee": {       'aliases': ['oee', 'hieu suat thiet bi', 'hieu suat oee', 'ti le oee', 'mesbcoee'],
        'column_labels': {       'a_rate': 'Tỷ lệ Sẵn sàng (A)',
                                 'ma_line': 'Mã Line/Máy',
                                 'oee': 'Chỉ số OEE (%)',
                                 'p_rate': 'Hiệu suất (P)',
                                 'q_rate': 'Chất lượng (Q)'},
        'default_params': {       'cma_dvcs': '001',
                                  'cma_line': '',
                                  'culture': 'vi-VN',
                                  'dfrom': '',
                                  'dto': '',
                                  'limit': 50,
                                  'offset': 0},
        'description': 'Tính toán chỉ số OEE (Hiệu suất tổng thể thiết bị) bao gồm Sẵn sàng (A), Hiệu suất (P) và Chất '
                       'lượng (Q).',
        'domain': 'SAN_XUAT',
        'id': 'mesbcoee',
        'procedure_name': 'mesbcoee',
        'summary_fields': [],
        'title': 'Báo cáo hiệu suất thiết bị toàn phần OEE'},

    "mesbksetup": {       'aliases': ['setup may', 'van hanh may', 'cai dat may', 'thoi gian setup', 'mesbksetup'],
        'column_labels': {       'ma_khuon': 'Mã khuôn',
                                 'ma_line': 'Mã máy',
                                 'ngay_ct': 'Ngày setup',
                                 'nguoi_setup': 'KTV thực hiện',
                                 'so_ct': 'Số phiếu',
                                 'tg_setup': 'Thời gian setup (phút)'},
        'default_params': {       'cma_dvcs': '001',
                                  'cma_line': '',
                                  'culture': 'vi-VN',
                                  'dfrom': '',
                                  'dto': '',
                                  'limit': 50,
                                  'offset': 0},
        'description': 'Nhật ký quá trình gá đặt khuôn, căn chỉnh thông số ép và chuẩn bị máy trước ca sản xuất.',
        'domain': 'SAN_XUAT',
        'id': 'mesbksetup',
        'procedure_name': 'mesbksetup',
        'summary_fields': ['tg_setup'],
        'title': 'Bảng kê setup và vận hành máy'},

    "mesbknglinhkien": {       'aliases': ['ng linh kien', 'loi linh kien', 'linh kien ng', 'mesbknglinhkien'],
        'column_labels': {       'ly_do': 'Nguyên nhân lỗi',
                                 'ma_vt': 'Mã linh kiện',
                                 'ngay_ct': 'Ngày ghi nhận',
                                 'so_ct': 'Số chứng từ',
                                 'so_luong': 'SL NG',
                                 'ten_vt': 'Tên linh kiện'},
        'default_params': {       'cma_dvcs': '001',
                                  'cma_line': '',
                                  'cma_vt': '',
                                  'culture': 'vi-VN',
                                  'dfrom': '',
                                  'dto': '',
                                  'limit': 50,
                                  'offset': 0},
        'description': 'Theo dõi chi tiết phế phẩm và linh kiện hỏng phát sinh trực tiếp tại từng dây chuyền / máy ép.',
        'domain': 'SAN_XUAT',
        'id': 'mesbknglinhkien',
        'procedure_name': 'mesbknglinhkien',
        'summary_fields': ['so_luong'],
        'title': 'Bảng kê lỗi linh kiện NG trong sản xuất'},

    "mfbklsx": {       'aliases': ['lenh san xuat', 'lsx', 'danh sach lenh san xuat', 'ke hoach lsx', 'mfbklsx'],
        'column_labels': {       'dvt': 'ĐVT',
                                 'ma_kh': 'Khách hàng',
                                 'ma_vt': 'Mã sản phẩm',
                                 'ngay_ct': 'Ngày lập',
                                 'so_ct': 'Số LSX',
                                 'so_dh': 'Đơn hàng (SO)',
                                 'so_luong': 'SL Kế hoạch',
                                 'status': 'Trạng thái',
                                 'ten_vt': 'Tên sản phẩm'},
        'default_params': {},
        'description': 'Danh sách lệnh sản xuất, số lượng giao khoán, đơn hàng khách hàng tương ứng và tiến độ hoàn '
                       'thành.',
        'domain': 'KE_HOACH',
        'id': 'mfbklsx',
        'procedure_name': None,
        'summary_fields': ['so_luong'],
        'title': 'Bảng kê lệnh sản xuất (LSX)'},

    "mfbkthongke": {       'aliases': ['thong ke san xuat', 'thong ke sx', 'tong hop san xuat', 'mfbkthongke'],
        'column_labels': {       'ma_vt': 'Mã SP',
                                 'ngay_ct': 'Ngày thống kê',
                                 'so_ct': 'Số chứng từ',
                                 'so_luong': 'SL Hoàn thành',
                                 'so_luong_ng': 'SL Phế phẩm'},
        'default_params': {       'cma_dvcs': '001',
                                  'cma_vt': '',
                                  'culture': 'vi-VN',
                                  'dfrom': '',
                                  'dto': '',
                                  'limit': 50,
                                  'offset': 0},
        'description': 'Tổng hợp kết quả sản lượng hoàn thành và tỷ lệ phế phẩm theo từng lệnh sản xuất.',
        'domain': 'KE_HOACH',
        'id': 'mfbkthongke',
        'procedure_name': 'mfbkthongke',
        'summary_fields': ['so_luong', 'so_luong_ng'],
        'title': 'Bảng kê thống kê sản xuất theo kỳ'},

    "mfbctieuhaonvltheolsx": {       'aliases': ['tieu hao nvl', 'tieu hao theo lsx', 'dinh muc tieu hao thuc te', 'mfbctieuhaonvltheolsx'],
        'column_labels': {       'chenh_lech': 'Chênh lệch',
                                 'ma_vt_nvl': 'Mã NVL',
                                 'ma_vt_sp': 'Mã SP',
                                 'sl_dinh_muc': 'SL Định mức',
                                 'sl_thuc_te': 'SL Thực xuất',
                                 'so_lsx': 'Số LSX',
                                 'ten_vt_nvl': 'Tên NVL'},
        'default_params': {       'cma_dvcs': '001',
                                  'cma_vt': '',
                                  'culture': 'vi-VN',
                                  'dfrom': '',
                                  'dto': '',
                                  'limit': 50,
                                  'offset': 0},
        'description': 'So sánh định mức nguyên vật liệu kế hoạch so với lượng xuất dùng thực tế trên mỗi lệnh sản '
                       'xuất.',
        'domain': 'KE_HOACH',
        'id': 'mfbctieuhaonvltheolsx',
        'procedure_name': 'mfbctieuhaonvltheolsx',
        'summary_fields': ['sl_dinh_muc', 'sl_thuc_te'],
        'title': 'Báo cáo tiêu hao NVL theo lệnh sản xuất'},

    "mfbcthnxtcd": {       'aliases': ['nxt cong doan', 'nhap xuat ton cong doan', 'ton cong doan', 'mfbcthnxtcd'],
        'column_labels': {       'ma_cd': 'Công đoạn',
                                 'ma_vt': 'Mã bán thành phẩm',
                                 'nhap': 'Nhập',
                                 'ten_vt': 'Tên chi tiết',
                                 'ton_cuoi': 'Tồn cuối',
                                 'ton_dau': 'Tồn đầu',
                                 'xuat': 'Xuất'},
        'default_params': {       'cma_dvcs': '001',
                                  'cma_vt': '',
                                  'culture': 'vi-VN',
                                  'dfrom': '',
                                  'dto': '',
                                  'limit': 50,
                                  'offset': 0},
        'description': 'Theo dõi lượng bán thành phẩm luân chuyển và tồn đọng tại từng trạm/công đoạn sản xuất.',
        'domain': 'KE_HOACH',
        'id': 'mfbcthnxtcd',
        'procedure_name': 'mfbcthnxtcd',
        'summary_fields': ['ton_dau', 'nhap', 'xuat', 'ton_cuoi'],
        'title': 'Báo cáo tổng hợp nhập xuất tồn công đoạn sản xuất'},

    "qcbkiqcipqc": {       'aliases': ['phieu iqc', 'phieu ipqc', 'kiem tra iqc', 'kiem tra ipqc', 'bien ban iqc', 'qcbkiqcipqc'],
        'column_labels': {       'ket_luan': 'Kết luận',
                                 'ma_ncc': 'Nhà cung cấp',
                                 'ma_vt': 'Mã vật tư',
                                 'ngay_ct': 'Ngày kiểm tra',
                                 'sl_ng': 'SL Lỗi (NG)',
                                 'sl_ok': 'SL Đạt (OK)',
                                 'so_ct': 'Số phiếu QC',
                                 'so_luong_lo': 'SL Lô kiểm',
                                 'ten_vt': 'Tên vật tư'},
        'default_params': {},
        'description': 'Chi tiết các biên bản đánh giá chất lượng nguyên liệu đầu vào và công đoạn ép nhựa.',
        'domain': 'CHAT_LUONG',
        'id': 'qcbkiqcipqc',
        'procedure_name': None,
        'summary_fields': ['so_luong_lo', 'sl_ok', 'sl_ng'],
        'title': 'Bảng kê phiếu kiểm tra IQC/IPQC chi tiết'},

    "qcbcthloinvl": {       'aliases': ['tong hop loi nvl', 'chi tieu loi nvl', 'loi nguyen vat lieu', 'qcbcthloinvl'],
        'column_labels': {       'ma_chi_tieu': 'Chỉ tiêu kiểm định',
                                 'ma_vt': 'Mã vật tư',
                                 'so_lan_loi': 'Số lần lỗi',
                                 'ti_le': 'Tỷ lệ lỗi (%)',
                                 'tong_so': 'Tổng số mẫu'},
        'default_params': {       'cma_dvcs': '001',
                                  'cma_vt': '',
                                  'culture': 'vi-VN',
                                  'dfrom': '',
                                  'dto': '',
                                  'limit': 50,
                                  'offset': 0},
        'description': 'Thống kê tần suất và tỷ lệ lỗi không đạt theo từng chỉ tiêu kỹ thuật của nguyên vật liệu.',
        'domain': 'CHAT_LUONG',
        'id': 'qcbcthloinvl',
        'procedure_name': 'qcbcthloinvl',
        'summary_fields': ['so_lan_loi', 'tong_so'],
        'title': 'Báo cáo tổng hợp lỗi chỉ tiêu nguyên vật liệu'},

    "qcbcthloitp": {       'aliases': ['tong hop loi tp', 'loi thanh pham', 'loi san pham', 'qcbcthloitp'],
        'column_labels': {       'ma_chi_tieu': 'Dạng lỗi',
                                 'ma_vt': 'Mã thành phẩm',
                                 'so_lan_loi': 'Số lần lỗi',
                                 'ti_le': 'Tỷ lệ (%)',
                                 'tong_so': 'Tổng kiểm'},
        'default_params': {       'cma_dvcs': '001',
                                  'cma_vt': '',
                                  'culture': 'vi-VN',
                                  'dfrom': '',
                                  'dto': '',
                                  'limit': 50,
                                  'offset': 0},
        'description': 'Thống kê các dạng lỗi xuất hiện trên thành phẩm xuất xưởng (ba-via, co ngót, biến dạng, trầy '
                       'xước).',
        'domain': 'CHAT_LUONG',
        'id': 'qcbcthloitp',
        'procedure_name': 'qcbcthloitp',
        'summary_fields': ['so_lan_loi', 'tong_so'],
        'title': 'Báo cáo tổng hợp lỗi sản phẩm sản xuất (TP)'},

    "dmhosokhuon": {       'aliases': [       'ho so khuon',
                           'danh muc khuon',
                           'thong so khuon',
                           'cavity khuon',
                           'kich thuoc khuon',
                           'so shot bao tri',
                           'dmhosokhuon'],
        'column_labels': {       'ma_khuon': 'Mã khuôn',
                                 'so_cavity': 'Số Cavity',
                                 'so_shot_baotri': 'Định mức bảo trì',
                                 'status': 'Trạng thái',
                                 'ten_khuon': 'Tên khuôn',
                                 'tong_so_shot': 'Tổng Shot dập',
                                 'vi_tri_khuon': 'Vị trí lưu'},
        'default_params': {},
        'description': 'Tra cứu thông số kỹ thuật khuôn: số cavity, kích thước, tổng số shot dập và ngưỡng bảo trì.',
        'domain': 'KHUON_THIET_BI',
        'id': 'dmhosokhuon',
        'procedure_name': None,
        'summary_fields': ['tong_so_shot'],
        'title': 'Danh mục hồ sơ kỹ thuật khuôn mẫu'},

    "dmhosokhuonsc": {       'aliases': ['sua chua khuon', 'bao tri khuon', 'lich su sua khuon', 'nhat ky sua khuon', 'dmhosokhuonsc'],
        'column_labels': {       'loai': 'Loại bảo trì',
                                 'ma_khuon': 'Mã khuôn',
                                 'ngay_nhan_yc': 'Ngày tiếp nhận',
                                 'noi_dung': 'Nội dung hư hỏng / sửa chữa',
                                 'noi_sua': 'Nơi sửa',
                                 'trang_thai': 'Tình trạng'},
        'default_params': {},
        'description': 'Nhật ký các đợt bảo dưỡng định kỳ, mài dao, phục hồi bề mặt và sửa chữa sự cố khuôn.',
        'domain': 'KHUON_THIET_BI',
        'id': 'dmhosokhuonsc',
        'procedure_name': None,
        'summary_fields': [],
        'title': 'Lịch sử bảo trì và sửa chữa khuôn mẫu'},

    "mesbcttdskhuon": {       'aliases': ['bao duong khuon', 'tinh trang khuon', 'canh bao bao tri khuon', 'mesbcttdskhuon'],
        'column_labels': {       'chenh_lech': 'Số shot còn lại',
                                 'khuyen_nghi': 'Khuyến nghị',
                                 'ma_khuon': 'Mã khuôn',
                                 'so_shot_baotri': 'Ngưỡng bảo trì',
                                 'ten_khuon': 'Tên khuôn',
                                 'tong_so_shot': 'Shot hiện tại'},
        'default_params': {},
        'description': 'Cảnh báo các bộ khuôn sắp chạm ngưỡng số shot bảo trì định kỳ để chuẩn bị kế hoạch dừng bảo '
                       'dưỡng.',
        'domain': 'KHUON_THIET_BI',
        'id': 'mesbcttdskhuon',
        'procedure_name': None,
        'summary_fields': [],
        'title': 'Báo cáo tình trạng bảo dưỡng khuôn định kỳ'},

}


def normalize_vietnamese(text: str) -> str:
    """Normalize Vietnamese text using standard unicodedata library."""
    import unicodedata
    import re
    if not text:
        return ""
    folded = unicodedata.normalize("NFD", text)
    folded = "".join(char for char in folded if unicodedata.category(char) != "Mn")
    folded = folded.replace("đ", "d").replace("Đ", "d").lower()
    return re.sub(r"[^a-z0-9]+", " ", folded).strip()


def find_report_in_catalog(query_or_intent: str) -> Optional[Dict[str, Any]]:
    """Resolve user query string or intent to the most appropriate report contract."""
    import re

    q = (query_or_intent or "").strip().lower()
    q_norm = normalize_vietnamese(q)
    q_words = set(q_norm.split())

    # 1. Exact catalog ID match
    if q in REPORT_CATALOG:
        return REPORT_CATALOG[q]

    # 2. Check each report's aliases
    scored_matches: List[tuple[int, Dict[str, Any]]] = []
    for report_id, report_meta in REPORT_CATALOG.items():
        score = 0
        for alias in report_meta.get("aliases", []):
            alias_norm = normalize_vietnamese(alias)
            alias_words = set(alias_norm.split())
            if re.search(r"\b" + re.escape(alias_norm) + r"\b", q_norm):
                # Exact full phrase match
                score = max(score, len(alias_words) * 15 + len(alias_norm))
            elif alias_norm in q_norm:
                score = max(score, len(alias_words) * 8)
            elif len(alias_words) >= 2 and alias_words.issubset(q_words):
                # All keywords of the alias appear in the query
                score = max(score, len(alias_words) * 6)
        
        # Title words subset match
        t_norm = normalize_vietnamese(report_meta.get("title", ""))
        t_words = set(t_norm.split()) - {"bao", "cao", "bang", "ke", "theo", "va", "cac", "trong", "tu", "cho"}
        if len(t_words) >= 2 and t_words.issubset(q_words):
            score = max(score, len(t_words) * 5)

        # Domain boost if domain matches
        if report_meta.get("domain", "").lower() in q_norm:
            score += 3
            
        if score > 0:
            scored_matches.append((score, report_meta))

    if scored_matches:
        scored_matches.sort(key=lambda x: x[0], reverse=True)
        return scored_matches[0][1]

    return None
