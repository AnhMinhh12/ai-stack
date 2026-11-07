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
            "hang ton", "muc ton", "bao cao ton kho"
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

    "inso1": {
        "id": "inso1",
        "domain": "KHO",
        "procedure_name": None,  # Handled directly via public.ct70
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
            "culture": "vi-VN"
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
            "cma_dvcs": "001", "culture": "vi-VN"
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
            "cma_kh": "",
            "cma_vt": "",
            "culture": "vi-VN"
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
            "limit": "50", "offset": "0", "culture": "vi-VN"
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

    # -------------------------------------------------------------
    # 4. CÔNG NỢ (AR / AP - DEBT)
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

    # -------------------------------------------------------------
    # 6. SẢN XUẤT & MES (MANUFACTURING / MES)
    # -------------------------------------------------------------
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
            "thung bao nhieu", "packs0", "tai khoan hp", "nhan vien", "hp4509", "4509"
        ],
        "description": "Quy cách đóng gói vật tư (số lượng/thùng, khay) hoặc tra cứu mã nhân viên hệ thống.",
        "column_labels": {
            "ma_vt": "Mã vật tư",
            "ten_vt": "Tên vật tư",
            "dvt": "ĐVT",
            "so_luong_thung": "SL/Thùng",
            "so_luong_khay": "SL/Khay",
            "ma_thung": "Mã thùng",
            "ma_khay": "Mã khay"
        },
        "summary_fields": []
    }
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

    # 1. Exact catalog ID match
    if q in REPORT_CATALOG:
        return REPORT_CATALOG[q]

    # 2. Check each report's aliases
    scored_matches: List[tuple[int, Dict[str, Any]]] = []
    for report_id, report_meta in REPORT_CATALOG.items():
        score = 0
        for alias in report_meta.get("aliases", []):
            alias_norm = normalize_vietnamese(alias)
            if re.search(r"\b" + re.escape(alias_norm) + r"\b", q_norm):
                # Longer alias matches get higher precedence
                score = max(score, len(alias_norm.split()) * 10 + len(alias_norm))
            elif alias_norm in q_norm:
                score = max(score, len(alias_norm.split()) * 5)
        
        # Domain boost if domain matches
        if report_meta.get("domain", "").lower() in q_norm:
            score += 5
            
        if score > 0:
            scored_matches.append((score, report_meta))

    if scored_matches:
        scored_matches.sort(key=lambda x: x[0], reverse=True)
        return scored_matches[0][1]

    return None
