"""
Module quản lý Từ điển siêu dữ liệu hệ thống ERP/MES (System Metadata Dictionary).
Được trích xuất trực tiếp từ các bảng cấu hình của 3S ERP: sys_dmtt, sys_gridconfig, sys_listoptions, sys_reports.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

_DICT_PATH = Path(__file__).resolve().parent.parent / "config" / "erp_metadata_dictionary.json"
_CACHE: Optional[Dict[str, Any]] = None

# Fallback column labels for common ERP fields if not found in gridconfig
_DEFAULT_LABELS = {
    "stt": "STT",
    "ma_vt": "Mã vật tư",
    "ten_vt": "Tên vật tư",
    "dvt": "ĐVT",
    "so_luong": "Số lượng",
    "so_luong_ton": "Số lượng tồn",
    "sl_ton": "Số lượng tồn",
    "sl_nhap": "Số lượng nhập",
    "sl_xuat": "Số lượng xuất",
    "ma_kho": "Mã kho",
    "ten_kho": "Tên kho",
    "ma_kh": "Mã khách hàng",
    "ten_kh": "Tên khách hàng",
    "ma_ncc": "Mã nhà cung cấp",
    "ten_ncc": "Tên nhà cung cấp",
    "ngay_ct": "Ngày chứng từ",
    "so_ct": "Số chứng từ",
    "ma_ct": "Mã chứng từ",
    "status": "Trạng thái",
    "status_name": "Tên trạng thái",
    "tien2": "Thành tiền (VND)",
    "tien_nt2": "Thành tiền (Nguyên tệ)",
    "gia2": "Đơn giá (VND)",
    "gia_nt2": "Đơn giá (Nguyên tệ)",
    "ma_nt": "Loại tiền",
    "ty_gia": "Tỷ giá",
    "dien_giai": "Diễn giải",
    "ma_lo": "Mã lô",
    "ngay_tao": "Ngày tạo",
    "nguoi_tao": "Người tạo",
    "ma_khuon": "Mã khuôn",
    "ten_khuon": "Tên khuôn",
    "so_shot": "Số shot",
    "so_shot_dm": "Shot định mức",
    "status_qc": "Trạng thái QC",
    "chi_tieu": "Chỉ tiêu",
    "hien_tai": "Kỳ hiện tại",
    "ban_truoc": "Kỳ trước",
    "chenh_lech": "Chênh lệch",
    "tong_cong": "Tổng cộng",
    "ti_le": "Tỷ lệ (%)",
    "ty_le": "Tỷ lệ (%)",
    "ghi_chu": "Ghi chú",
    "ma_may": "Mã máy",
    "ten_may": "Tên máy",
    "ma_loi": "Mã lỗi",
    "ten_loi": "Tên lỗi",
    "nguyen_nhan": "Nguyên nhân",
    "thoi_gian_dung": "Thời gian dừng (phút)",
    "so_thung": "Số thùng",
    "so_pallet": "Số pallet",
}

def load_dictionary() -> Dict[str, Any]:
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    if _DICT_PATH.exists():
        try:
            with open(_DICT_PATH, "r", encoding="utf-8") as f:
                _CACHE = json.load(f)
                return _CACHE
        except Exception:
            pass
    return {}

def get_document_status_name(ma_ct: str, status_code: Any) -> str:
    """Trả về tên hiển thị tiếng Việt của trạng thái chứng từ (từ sys_dmtt)."""
    dic = load_dictionary()
    doc_types = dic.get("document_statuses", {})
    ct_info = doc_types.get(str(ma_ct).strip().upper(), {})
    st_info = ct_info.get(str(status_code).strip())
    if isinstance(st_info, dict) and st_info.get("label"):
        return st_info["label"]
    return str(status_code)

def get_valid_statuses(ma_ct: str) -> List[str]:
    """Trả về danh sách trạng thái hợp lệ (loại trừ từ chối deny_yn=1 hoặc hủy)."""
    dic = load_dictionary()
    doc_types = dic.get("document_statuses", {})
    ct_info = doc_types.get(str(ma_ct).strip().upper(), {})
    valid = []
    for st_code, st_meta in ct_info.items():
        if isinstance(st_meta, dict):
            if not st_meta.get("is_denied") and st_code not in ("14", "15"):
                valid.append(st_code)
    return valid

def get_column_caption(field_name: str, grid_id: Optional[str] = None) -> str:
    """Trả về nhãn tiếng Việt hiển thị của cột trên giao diện ERP (từ sys_gridconfig)."""
    field_clean = str(field_name).strip().lower()
    dic = load_dictionary()
    grids = dic.get("grids", {})
    
    # 1. Tìm theo grid_id cụ thể nếu có
    if grid_id and grid_id in grids:
        for col in grids[grid_id].get("columns", []):
            if col.get("field", "").lower() == field_clean and col.get("caption"):
                return col["caption"]
    
    # 2. Tìm nhanh trong các grid phổ biến
    for gid in ("HDA", "SO1", "TO2", "PO1", "CT70", "cdvt", "dmvt"):
        if gid in grids:
            for col in grids[gid].get("columns", []):
                if col.get("field", "").lower() == field_clean and col.get("caption"):
                    return col["caption"]
    
    # 3. Fallback theo từ điển mặc định
    return _DEFAULT_LABELS.get(field_clean, field_name)

def get_visible_grid_columns(grid_id: str) -> List[Dict[str, Any]]:
    """Lấy danh sách đầy đủ các cột hiển thị trên UI của một lưới/màn hình."""
    dic = load_dictionary()
    grids = dic.get("grids", {})
    if grid_id in grids:
        return grids[grid_id].get("columns", [])
    return []

def get_list_option_text(form_name: str, opt_val: Any) -> str:
    """Lấy nhãn tùy chọn tiếng Việt (sys_listoptions)."""
    dic = load_dictionary()
    forms = dic.get("list_options", {})
    finfo = forms.get(str(form_name).strip().upper(), {})
    vinfo = finfo.get(str(opt_val).strip())
    if isinstance(vinfo, dict) and vinfo.get("label"):
        return vinfo["label"]
    return str(opt_val)

