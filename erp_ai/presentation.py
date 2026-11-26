"""Deterministic ERP display blocks built only from verified tool results."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from html import escape
import json
from .system_dictionary import get_column_caption
from .validator import validate_inventory_balance_result

LOOKUP_TITLES = {
    "query_price_list": "Danh mục bảng giá và MOQ",
    "query_bom_structure": "Cấu trúc sản phẩm & định mức BOM",
    "query_customer_info": "Danh mục khách hàng",
    "query_employee_info": "Danh mục nhân viên và tài khoản ERP",
    "query_material_customer": "Khách hàng khai báo trên mã vật tư",
    "query_forecast_po": "Kế hoạch PO và dự báo FCST",
    "query_packaging_spec": "Quy cách đóng gói vật tư sản phẩm",
    "query_mold_profile": "Hồ sơ thiết bị khuôn và tuổi thọ shot",
    "query_mold_label_stock": "Tồn kho theo số khuôn và die_no",
    "query_sales_order_price_gaps": "Mã hàng ứng viên thiếu liên kết giá chuẩn",
    "query_delivery_order": "Trạng thái lệnh giao hàng (TO2)",
    "query_qc_status": "Tồn kho theo trạng thái tem QC",
    "query_replacement_orders": "Lệnh giao hàng giao bù NG",
}

LOOKUP_FIELD_META = {
    "ma_kh": ("Mã đối tượng", "text"),
    "ten_kh": ("Tên đối tượng", "text"),
    "ten_viet_tat": ("Tên viết tắt", "text"),
    "loai_ho_so": ("Loại hồ sơ", "text"),
    "ma_nv": ("Mã NV / User", "text"),
    "ten_nv": ("Họ và tên", "text"),
    "ma_bp": ("Bộ phận", "text"),
    "chuc_vu": ("Chức vụ", "text"),
    "trang_thai": ("Trạng thái", "text"),
    "nv_yn": ("Nhân viên", "number"),
    "kh_yn": ("Khách hàng", "number"),
    "cc_yn": ("Nhà cung cấp", "number"),
    "dien_thoai": ("Điện thoại", "text"),
    "dia_chi": ("Địa chỉ", "text"),
    "ma_vt": ("Mã vật tư", "text"),
    "ten_vt": ("Tên vật tư", "text"),
    "ma_sp": ("Mã sản phẩm", "text"),
    "ma_sp_me": ("Mã SP mẹ", "text"),
    "material_code": ("Mã NVL", "text"),
    "bom_code": ("Mã BOM", "text"),
    "bom_version": ("Phiên bản BOM", "text"),
    "sl_dinh_muc": ("Định mức", "number"),
    "valid_from": ("Hiệu lực từ", "date"),
    "valid_to": ("Hiệu lực đến", "date"),
    "sl_min": ("MOQ", "number"),
    "gia0": ("Giá trước VAT", "number"),
    "gia": ("Đơn giá", "number"),
    "ma_nt": ("Loại tiền", "text"),
    "ngay_bd": ("Ngày bắt đầu", "date"),
    "ngay_kt": ("Ngày kết thúc", "date"),
    "dvt": ("ĐVT", "text"),
    "status": ("Trạng thái", "text"),
    "statusname": ("Tên trạng thái", "text"),
    "id": ("ID", "text"),
    "stt": ("STT", "number"),
    "ngay_giao_hang": ("Ngày giao hàng", "date"),
    "ngay_tinh_toan": ("Ngày tính toán", "date"),
    "so_luong": ("Số lượng", "number"),
    "nguon_du_lieu": ("Nguồn dữ liệu", "text"),
    "loai_du_lieu": ("Loại dữ liệu", "text"),
    "model": ("Model", "text"),
    "so_ct": ("Số chứng từ", "text"),
    "stt_rec": ("Mã chứng từ", "text"),
    "ngay_ct": ("Ngày chứng từ", "date"),
    "date0": ("Ngày lập", "date"),
    "time0": ("Giờ lập", "text"),
    "packs": ("Quy cách thùng", "number"),
    "packs0": ("SL/thùng (packs0)", "number"),
    "ma_thung": ("Mã thùng", "text"),
    "ma_khay": ("Mã khay", "text"),
    "so_luong_vt_khay": ("SL vật tư/khay", "number"),
    "so_luong_thung_pallet": ("SL thùng/pallet", "number"),
    "so_luong_sp_tui": ("SL SP/túi", "number"),
    "ma_khuon": ("Mã khuôn", "text"),
    "ten_khuon": ("Tên khuôn", "text"),
    "tong_so_shot": ("Tổng số shot đã chạy", "number"),
    "so_shot_bh": ("Số shot định mức BH", "number"),
    "die_no": ("Số lòng khuôn (die_no)", "text"),
    "status_qc": ("Mã QC", "text"),
    "trang_thai_qc": ("Trạng thái QC", "text"),
    "so_tem": ("Số tem", "number"),
    "order_lines": ("Số dòng ĐH", "number"),
    "null_price_lines": ("Số dòng giá NULL", "number"),
    "zero_price_lines": ("Số dòng giá = 0", "number"),
    "ma_gd": ("Mã giao dịch", "text"),
    "dien_giai": ("Diễn giải", "text"),
}


SEMANTIC_DATASET_TITLES = {
    "sales_delivery_lines": "Tổng hợp xuất kho bán hàng",
    "sales_order_lines": "Tổng hợp đơn hàng bán (SO)",
    "purchase_order_lines": "Tổng hợp đơn hàng mua (PO)",
    "purchase_requests": "Phiếu yêu cầu / đề nghị mua hàng (PR0)",
    "purchase_receipt_lines": "Tổng hợp nhập mua hàng",
    "inventory_movements": "Tổng hợp xuất nhập kho",
    "mes_downtime_lines": "Thống kê dừng máy (MES)",
    "mes_ng_defects": "Thống kê lỗi NG (MES)",
    "qc_iqc_lines": "Thống kê kiểm tra đầu vào (IQC)",
    "mes_production_output": "Sản lượng sản xuất MES",
    "mes_work_orders": "Lệnh sản xuất & tiến độ WO",
    "mes_oee_daily": "Chỉ số vận hành & OEE theo máy",
    "mes_material_usage": "Cấp & tiêu hao nguyên vật liệu (MES)",
    "mold_cavity_specs": "Hồ sơ Khuôn - Cavity - Chu kỳ",
    "production_forecast_demand": "Kế hoạch PO & Dự báo FCST",
    "gl_account_movements": "Phát sinh sổ cái & công nợ (ct00)",
}

SEMANTIC_FIELD_META = {
    "customer": ("Mã KH", "text"),
    "customer_name": ("Tên khách hàng", "text"),
    "supplier": ("Mã NCC", "text"),
    "supplier_name": ("Tên nhà cung cấp", "text"),
    "po_no": ("Số đơn PO", "text"),
    "pr_no": ("Số phiếu ĐNMH", "text"),
    "department": ("Bộ phận", "text"),
    "requester": ("Mã người đề nghị", "text"),
    "requester_name": ("Người đề nghị", "text"),
    "in_charge": ("Mã người phụ trách", "text"),
    "in_charge_name": ("Người phụ trách", "text"),
    "creator_user": ("User tạo phiếu", "text"),
    "creator_name": ("Tên người tạo", "text"),
    "status": ("Trạng thái", "text"),
    "material": ("Mã vật tư", "text"),
    "material_name": ("Tên vật tư", "text"),
    "product": ("Mã thành phẩm", "text"),
    "product_name": ("Tên thành phẩm", "text"),
    "warehouse": ("Mã kho", "text"),
    "warehouse_name": ("Tên kho", "text"),
    "machine": ("Mã máy", "text"),
    "line_group": ("Nhóm máy", "text"),
    "shift": ("Ca SX", "text"),
    "work_order": ("Lệnh SX (WO)", "text"),
    "schedule_code": ("Mã lịch SX", "text"),
    "mold": ("Mã khuôn", "text"),
    "mold_name": ("Tên khuôn", "text"),
    "wo_status": ("Trạng thái WO", "text"),
    "work_center": ("Phân xưởng", "text"),
    "step": ("Công đoạn", "text"),
    "station": ("Trạm SX", "text"),
    "cavity_group": ("Nhóm cavity", "text"),
    "primary_flag": ("Chính/Phụ", "text"),
    "demand_type": ("Loại nhu cầu", "text"),
    "data_source": ("Nguồn dữ liệu", "text"),
    "model": ("Model", "text"),
    "account": ("Tài khoản", "text"),
    "account_name": ("Tên tài khoản", "text"),
    "offset_account": ("TK đối ứng", "text"),
    "partner": ("Mã đối tượng", "text"),
    "partner_name": ("Tên đối tượng", "text"),
    "reason_code": ("Mã nguyên nhân", "text"),
    "reason_name": ("Nguyên nhân dừng máy", "text"),
    "reason_group": ("Nhóm nguyên nhân", "text"),
    "defect_code": ("Mã lỗi", "text"),
    "defect_name": ("Tên lỗi NG", "text"),
    "qc_result": ("Kết quả IQC", "text"),
    "doc_type": ("Loại chứng từ", "text"),
    "currency": ("Loại tiền", "text"),
    "unit": ("ĐVT", "text"),
    "day": ("Ngày", "date"),
    "required_date": ("Ngày nhận hàng", "date"),
    "quantity": ("Số lượng", "number"),
    "revenue_vnd": ("Doanh thu (VND)", "number"),
    "revenue_orig": ("Doanh thu (NT)", "number"),
    "delivery_count": ("Số phiếu xuất", "number"),
    "amount_vnd": ("Thành tiền (VND)", "number"),
    "amount_orig": ("Thành tiền (NT)", "number"),
    "avg_price_vnd": ("Đơn giá TB (VND)", "number"),
    "order_count": ("Số đơn hàng", "number"),
    "orders": ("Số đơn", "number"),
    "po_count": ("Số đơn PO", "number"),
    "pr_count": ("Số phiếu ĐNMH", "number"),
    "receipt_count": ("Số phiếu nhập", "number"),
    "in_qty": ("SL nhập", "number"),
    "out_qty": ("SL xuất", "number"),
    "in_amount_vnd": ("Tiền nhập (VND)", "number"),
    "out_amount_vnd": ("Tiền xuất (VND)", "number"),
    "tx_count": ("Số giao dịch", "number"),
    "stop_minutes": ("Thời gian dừng (phút)", "number"),
    "avg_stop_minutes": ("TB dừng (phút)", "number"),
    "stop_count": ("Số lần dừng", "number"),
    "ng_qty": ("Số lượng NG", "number"),
    "defect_events": ("Số lượt lỗi", "number"),
    "inspection_count": ("Số lượt kiểm tra", "number"),
    "lot_qty": ("Tổng SL lô", "number"),
    "ok_qty": ("SL đạt", "number"),
    "planned_qty": ("SL kế hoạch", "number"),
    "complete_qty": ("SL hoàn thành", "number"),
    "packing_qty": ("SL đóng gói", "number"),
    "skip_shot": ("SL bỏ shot", "number"),
    "run_minutes": ("Thời gian chạy (phút)", "number"),
    "run_count": ("Số phiên chạy", "number"),
    "wo_count": ("Số lệnh WO", "number"),
    "cavity": ("Số cavity", "number"),
    "cycle_time": ("Chu kỳ KH (giây)", "number"),
    "cycle_sec": ("Chu kỳ khuôn (giây)", "number"),
    "efficiency": ("Hiệu suất (%)", "number"),
    "net_minutes": ("Thời gian chạy thực (phút)", "number"),
    "standard_minutes": ("Thời gian chuẩn (phút)", "number"),
    "availability_pct": ("Khả dụng A (%)", "number"),
    "performance_pct": ("Hiệu suất P (%)", "number"),
    "quality_pct": ("Chất lượng Q (%)", "number"),
    "oee_pct": ("OEE (%)", "number"),
    "line_days": ("Số ngày máy", "number"),
    "required_qty": ("SL cần cấp", "number"),
    "issued_qty": ("SL đã cấp", "number"),
    "used_qty": ("SL sử dụng", "number"),
    "remaining_qty": ("SL còn lại", "number"),
    "variance_qty": ("SL chênh lệch", "number"),
    "feed_count": ("Số lần cấp NVL", "number"),
    "total_shots": ("Tổng số shot đã chạy", "number"),
    "warranty_shots": ("Shot định mức BH", "number"),
    "remaining_warranty_shots": ("Shot BH còn lại", "number"),
    "product_links": ("Số mã SP gắn khuôn", "number"),
    "line_count": ("Số dòng KH", "number"),
    "debit_vnd": ("Phát sinh Nợ (VND)", "number"),
    "credit_vnd": ("Phát sinh Có (VND)", "number"),
    "debit_orig": ("Phát sinh Nợ (NT)", "number"),
    "credit_orig": ("Phát sinh Có (NT)", "number"),
    "voucher_count": ("Số chứng từ", "number"),
    "doc_no": ("Số chứng từ", "text"),
    "status_name": ("Trạng thái", "text"),
    "delivery_date": ("Ngày giao hàng", "date"),
    "expiry_date": ("Hạn sử dụng", "date"),
    "mfg_date": ("Ngày sản xuất", "date"),
    "valid_from": ("Hiệu lực từ", "date"),
    "valid_to": ("Hiệu lực đến", "date"),
    "last_maint_date": ("Ngày bảo dưỡng cuối", "date"),
    "so_no": ("Số đơn bán (SO)", "text"),
    "po_kh": ("Số PO khách hàng", "text"),
    "lot_no": ("Số lô", "text"),
    "location": ("Vị trí kho", "text"),
    "target_warehouse": ("Kho nhận", "text"),
    "target_warehouse_name": ("Tên kho nhận", "text"),
    "stock_qty": ("SL tồn kho", "number"),
    "return_qty": ("SL trả lại", "number"),
    "transfer_qty": ("SL điều chuyển", "number"),
    "pending_qty": ("SL còn pending", "number"),
    "bom_qty": ("Định mức BOM", "number"),
    "loss_pct": ("Tỷ lệ hao hụt (%)", "number"),
    "unit_price_vnd": ("Đơn giá (VND)", "number"),
    "unit_price_orig": ("Đơn giá (NT)", "number"),
    "moq": ("SL tối thiểu (MOQ)", "number"),
    "bom_code": ("Mã BOM", "text"),
    "bom_version": ("Phiên bản BOM", "text"),
    "change_type": ("Loại thay đổi", "text"),
    "change_count": ("Số lần thay đổi", "number"),
    "ecn_no": ("Số ECN", "text"),
    "setup_minutes": ("Thời gian setup (phút)", "number"),
    "setup_count": ("Số lượt setup", "number"),
    "mold_op_count": ("Số lượt lên/xuống khuôn", "number"),
    "employee_code": ("Mã nhân viên", "text"),
    "employee_name": ("Tên nhân viên", "text"),
    "actual_qty": ("SL thực hiện", "number"),
    "operator_count": ("Số nhân sự", "number"),
    "carton_count": ("Số thùng đóng gói", "number"),
    "box_code": ("Mã thùng", "text"),
    "skip_shots": ("Số shot bỏ", "number"),
    "skip_qty": ("SL sản phẩm bỏ shot", "number"),
    "schedule_qty": ("SL kế hoạch điều độ", "number"),
    "pqc_count": ("Số phiếu PQC", "number"),
    "incident_type": ("Loại sự cố khuôn", "text"),
    "incident_detail": ("Chi tiết sự cố", "text"),
    "mold_count": ("Số khuôn", "number"),
    "stock_type": ("Loại tồn kho", "text"),
    "pending_type": ("Nhóm vật tư pending", "text"),
    "request_type": ("Loại phiếu YC", "text"),
    "confirmed_delivery_date": ("Ngày NCC xác nhận giao", "date"),
    "requested_date": ("Ngày đề nghị nhận hàng", "date"),
    "promise_date": ("Ngày NCC hứa giao", "date"),
    "price_list_id": ("Mã bảng giá", "text"),
    "price_list_name": ("Tên bảng giá", "text"),
    "pallet_id": ("Mã Pallet", "text"),
    "pallet_serial": ("Serial tem Pallet", "text"),
    "carton_serial": ("Serial tem thùng", "text"),
    "pallet_count": ("Số Pallet", "number"),
    "packed_qty": ("SL đã đóng gói", "number"),
    "serial_tem": ("Serial tem", "text"),
    "label_count": ("Số tem/serial", "number"),
    "entry_type": ("Loại giao dịch/ghi nhận", "text"),
    "txn_code": ("Mã nhập xuất (NX)", "text"),
    "drawing_code": ("Mã bản vẽ", "text"),
    "model": ("Model", "text"),
    "part_weight": ("Trọng lượng SP", "number"),
    "runner_weight": ("Trọng lượng runner", "number"),
    "tooling_life": ("Tuổi thọ khuôn", "number"),
    "cost_vnd": ("Tổng chi phí (VND)", "number"),
    "material_cost": ("Chi phí NVL", "number"),
    "mold_cost": ("Chi phí khuôn", "number"),
    "unit_price_usd": ("Đơn giá (USD)", "number"),
    "leadtime": ("Leadtime chuẩn (ngày)", "number"),
    "leadtime_kfc": ("Leadtime KFC (ngày)", "number"),
    "regen_ratio": ("Tỷ lệ tái sinh (%)", "number"),
    "mixing_ratio": ("Tỷ lệ trộn (%)", "number"),
    "gate_runner_qty": ("SL gate/runner", "number"),
    "alt_material": ("Vật tư thay thế", "text"),
    "operation_code": ("Mã nguyên công", "text"),
    "item_type": ("Nhóm vật tư", "text"),
    "shortage_qty": ("SL thiếu/yêu cầu", "number"),
    "ng_stock_qty": ("SL tồn NG", "number"),
    "impurity_qty": ("SL tạp chất", "number"),
    "prepare_qty": ("SL NVL chuẩn bị", "number"),
    "needed_qty": ("SL cần cấp", "number"),
    "feed_round": ("Lần cấp", "number"),
    "inbound_qty": ("SL bàn giao công đoạn", "number"),
    "add_qty": ("SL bù/điều chỉnh", "number"),
    "inbound_count": ("Số lượt bàn giao", "number"),
    "pause_count": ("Số lần tạm dừng", "number"),
    "cavity_changes": ("Số lần đổi cavity", "number"),
    "event_type": ("Loại sự kiện MES", "text"),
    "criterion_code": ("Mã chỉ tiêu QC", "text"),
    "criterion_name": ("Tên chỉ tiêu QC", "text"),
    "eval_result": ("Đánh giá chỉ tiêu", "text"),
    "qc_doc_type": ("Loại kiểm tra (IQC/PQC)", "text"),
    "check_count": ("Số lượt đo kiểm", "number"),
    "fc_code": ("Mã đợt Forecast", "text"),
    "fc_type": ("Kiểu Forecast", "text"),
    "period_type": ("Chu kỳ Forecast", "text"),
    "supplier_short": ("NCC viết tắt", "text"),
}


# Default presentation metadata used only when callers omit `config` (e.g. unit tests).
_DEFAULT_REPORT_PRESENTATIONS = {
    "query_inventory_balance": {"mode": "scalar_inventory"},
    "query_allowed_records": {
        "mode": "table",
        "title": "Bảng kê phiếu xuất kho bán hàng",
        "scope_template": "mã {material}, {date_from} đến {date_to}",
        "empty_text": "Không có phiếu xuất kho bán hàng cho {scope}.",
        "summary_noun": "dòng xuất bán",
        "fallback_summary_verb": "đã trích xuất",
        "summary_revenue": True,
        "filter_keys": ["material", "date_from", "date_to"],
        "sort": [{"key": "ngay_ct", "direction": "desc"}, {"key": "so_ct", "direction": "desc"}],
        "columns": [
            {"key": "ngay_ct", "label": "Ngày xuất", "type": "date"},
            {"key": "so_ct", "label": "Số chứng từ", "type": "text"},
            {"key": "ma_kh", "label": "Mã khách hàng", "type": "text"},
            {"key": "ma_vt", "label": "Mã vật tư", "type": "text"},
            {"key": "ma_kho", "label": "Kho xuất", "type": "text"},
            {"key": "dvt", "label": "ĐVT", "type": "text"},
            {"key": "so_luong", "label": "Số lượng", "type": "number"},
            {"key": "tien2", "label": "Thành tiền (VND)", "type": "number"},
        ],
    },
    "query_sales_orders": {
        "mode": "table",
        "title": "Bảng kê đơn hàng bán (SO1)",
        "scope_template": "khách hàng {customer}, từ {date_from} đến {date_to}",
        "empty_text": "Không có đơn hàng bán nào của {scope}.",
        "summary_noun": "dòng đơn hàng",
        "filter_keys": ["customer", "date_from", "date_to"],
        "sort": [{"key": "ngay_ct", "direction": "desc"}, {"key": "so_ct", "direction": "desc"}],
        "columns": [
            {"key": "ngay_ct", "label": "Ngày đơn hàng", "type": "date"},
            {"key": "so_ct", "label": "Số đơn hàng", "type": "text"},
            {"key": "ma_kh", "label": "Mã khách", "type": "text"},
            {"key": "ma_vt", "label": "Mã vật tư", "type": "text"},
            {"key": "dvt", "label": "ĐVT", "type": "text"},
            {"key": "so_luong", "label": "Số lượng", "type": "number"},
            {"key": "gia2", "label": "Đơn giá", "type": "number"},
            {"key": "gia_chuan", "label": "Giá chuẩn", "type": "number"},
            {"key": "status", "label": "Trạng thái", "type": "text"},
        ],
    },
    "query_inventory_by_warehouse": {
        "mode": "table",
        "title": "Báo cáo tồn kho theo từng kho",
        "scope_template": "mã {material} tính đến {date_as_of}",
        "empty_text": "Không tìm thấy số dư tồn kho theo kho cho {scope}.",
        "summary_mode": "warehouse_balance",
        "filter_keys": ["material", "date_as_of"],
        "columns": [
            {"key": "ma_kho", "label": "Mã kho", "type": "text"},
            {"key": "ten_kho", "label": "Tên kho", "type": "text"},
            {"key": "dvt", "label": "ĐVT", "type": "text"},
            {"key": "so_luong_ton", "label": "Số lượng tồn", "type": "number"},
        ],
    },
    "query_receipt_lines": {
        "mode": "table",
        "title": "Lịch sử nhập kho",
        "scope_template": "mã {material}, {date_from} đến {date_to}",
        "empty_text": "Không có giao dịch nhập kho cho {scope}.",
        "empty_unknown_text": "Chưa có dòng dữ liệu cho {scope}.",
        "summary_noun": "dòng nhập kho",
        "fallback_summary_verb": "đã nhận",
        "filter_keys": ["material", "date_from", "date_to"],
        "sort": [{"key": "ngay_ct", "direction": "desc"}, {"key": "so_ct", "direction": "desc"}],
        "columns": [
            {"key": "ngay_ct", "label": "Ngày nhập", "type": "date"},
            {"key": "so_ct", "label": "Số chứng từ", "type": "text"},
            {"key": "ma_kho", "label": "Kho nhận", "type": "text"},
            {"key": "kho_xuat", "label": "Kho xuất chuyển", "type": "text"},
            {"key": "sl_nhap", "label": "Số lượng", "type": "number"},
            {"key": "dvt", "label": "Đơn vị", "type": "text"},
            {"key": "nguoi_nhap", "label": "Người nhập", "type": "text"},
        ],
        "chart": {
            "value_field": "sl_nhap",
            "unit_field": "dvt",
            "date_field": "ngay_ct",
            "group_field": "ma_kho",
            "date_label": "Ngày nhập",
            "group_label": "Kho nhận",
            "series_label": "Số lượng nhập",
        },
    },
}


class _DefaultMissing(dict):
    def __missing__(self, key):
        return "?"


def _value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _cell(value):
    if value is None or value == "":
        return "—"
    return escape(str(_value(value)), quote=False).replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ").replace("\r", " ")


def _format_qty(qty):
    if qty is None:
        return ""
    try:
        val = float(qty)
        if val.is_integer():
            return f"{int(val):,}"
        return f"{val:,.2f}".rstrip("0").rstrip(".")
    except (ValueError, TypeError):
        return str(qty)


def _infer_columns(rows, custom_labels):
    """Build column descriptors from config labels, known metadata, or row sample types."""
    hidden = {"total_lines", "total_quantity", "total_revenue", "total"}
    keys = [k for k in rows[0] if k not in hidden] or list(rows[0])
    columns = []
    for key in keys:
        if key in custom_labels:
            lbl = custom_labels[key]
            sample = next((r.get(key) for r in rows if r.get(key) is not None), None)
            col_type = "date" if isinstance(sample, (date, datetime)) else ("number" if isinstance(sample, (int, float, Decimal)) and not isinstance(sample, bool) else "text")
        elif key in LOOKUP_FIELD_META:
            lbl, col_type = LOOKUP_FIELD_META[key]
        elif key in SEMANTIC_FIELD_META:
            lbl, col_type = SEMANTIC_FIELD_META[key]
        else:
            sample = next((r.get(key) for r in rows if r.get(key) is not None), None)
            if isinstance(sample, (date, datetime)):
                col_type = "date"
            elif isinstance(sample, (int, float, Decimal)) and not isinstance(sample, bool):
                col_type = "number"
            else:
                col_type = "text"
            lbl = get_column_caption(key)
        columns.append({"key": key, "label": lbl, "type": col_type})
    return columns


def _scalar_inventory_blocks(item):
    """Render deterministic single-stock balance summary from verified inventory row."""
    result = item["result"]
    rows = result.get("rows", [])
    material = item["arguments"]["material"]
    date_as_of = item["arguments"].get("date_as_of", "?")
    if not rows:
        label = f"Không tìm thấy tồn kho sổ sách của mã {material} tính đến {date_as_of}."
    elif not result.get("has_more") and validate_inventory_balance_result(material, rows) is None:
        quantity = format(Decimal(str(rows[0]["so_luong_ton"])).normalize(), "f")
        unit = rows[0].get("dvt") or ""
        label = f"Tồn kho sổ sách của mã {material} tính đến {date_as_of}: {quantity}{' ' + unit if unit else ''}."
    else:
        label = f"Chưa xác định được số lượng tồn kho sổ sách của mã {material} tính đến {date_as_of} từ kết quả này."
    return [{"type": "summary", "text": label, "source_ids": [s["id"] for s in result.get("sources", [])]}]


def _table_chart_block(question, rows, pres, quantity, has_more, source_ids):
    """Build deterministic chart and optional truncation warning from configured chart metadata."""
    chart_cfg = pres.get("chart")
    if not (rows and isinstance(chart_cfg, dict)):
        return []
    value_field = chart_cfg.get("value_field")
    if not value_field:
        return []
    unit_field = chart_cfg.get("unit_field")
    units = {str(row.get(unit_field) or "") for row in rows} if unit_field else {""}
    if len(units) != 1:
        return []
    date_field = chart_cfg.get("date_field", "ngay_ct")
    group_field = chart_cfg.get("group_field", "ma_kho")
    date_label = chart_cfg.get("date_label", "Ngày")
    group_label = chart_cfg.get("group_label", "Nhóm")
    series_label = chart_cfg.get("series_label", "Số lượng")
    days = {str(_value(row.get(date_field))) for row in rows}
    lowered = (question or "").lower()
    wants_share = any(t in lowered for t in ("tỷ trọng", "ty trong", "cơ cấu", "co cau", "phần trăm", "phan tram", "biểu đồ tròn", "bieu do tron", "pie"))
    wants_group = any(t in lowered for t in ("biểu đồ theo kho", "bieu do theo kho", "theo từng kho", "theo tung kho", "so sánh các kho", "so sanh cac kho", "theo nhóm", "theo nhom"))
    if wants_share or wants_group or len(days) == 1:
        key, x_label = group_field, group_label
    else:
        key, x_label = date_field, date_label
    grouped = defaultdict(float)
    for row in rows:
        lbl = str(_value(row.get(key)) or "")
        try:
            grouped[lbl] += float(row[value_field])
        except (KeyError, TypeError, ValueError):
            grouped.clear()
            break
    blocks = []
    matches_total = has_more or quantity is None or abs(sum(grouped.values()) - quantity) < 1e-6
    if len(grouped) > 1 and matches_total:
        chart_scope = f"{len(rows)} dòng đang hiển thị" if has_more else "Toàn bộ dòng trong bảng"
        can_pie = (wants_share and not has_more and key == group_field
                   and 2 <= len(grouped) <= 8 and all(value >= 0 for value in grouped.values())
                   and sum(grouped.values()) > 0 and quantity is not None)
        pie_available = (not has_more and 2 <= len(grouped) <= 8
                         and all(value >= 0 for value in grouped.values())
                         and sum(grouped.values()) > 0 and quantity is not None)
        chart_type = "pie" if can_pie else "line" if key == date_field else "bar"
        title = (f"Tỷ trọng {series_label.lower()} theo {group_label.lower()}"
                 if can_pie else f"{series_label} theo {x_label.lower()}")
        blocks.append({
            "type": "chart", "chart_type": chart_type,
            "allowed_chart_types": ["bar", "line", *(["pie"] if pie_available else [])],
            "title": title,
            "x": {"key": "category", "label": x_label, "type": "date" if key == date_field else "text"},
            "series": [{"key": "quantity", "label": series_label, "unit": next(iter(units))}],
            "points": [{"category": lbl, "quantity": value} for lbl, value in sorted(grouped.items())],
            "scope": chart_scope, "source_ids": source_ids,
        })
    if wants_share and has_more:
        blocks.append({"type": "warning", "text": "Chưa vẽ biểu đồ tròn vì bảng chỉ có một phần giao dịch; biểu đồ so sánh (nếu có) chỉ dùng các dòng đang hiển thị.", "source_ids": source_ids})
    return blocks


def _configured_table_blocks(question, item, pres, report):
    """Build declarative summary, table, and optional chart blocks for a configured report."""
    result = item["result"]
    rows = result.get("rows", [])
    summary = result.get("summary", {})
    source_ids = [s["id"] for s in result.get("sources", [])]
    filters = item.get("arguments", {})
    safe_filters = _DefaultMissing({k: v if v not in (None, "") else "?" for k, v in filters.items()})
    title = pres.get("title") or report.get("title") or LOOKUP_TITLES.get(item.get("tool") or "", "Kết quả tra cứu")
    scope = (pres.get("scope_template") or "").format_map(safe_filters) if pres.get("scope_template") else title
    total = summary.get("total_records")
    quantity = summary.get("total_quantity")
    revenue = summary.get("total_revenue")
    has_more = bool(result.get("has_more"))
    if not rows:
        if total != 0 and pres.get("empty_unknown_text"):
            label = pres["empty_unknown_text"].format(scope=scope)
        else:
            label = (pres.get("empty_text") or f"Không tìm thấy dữ liệu cho {scope}.").format(scope=scope)
    elif pres.get("summary_mode") == "warehouse_balance":
        unit = rows[0].get("dvt") or ""
        label = f"Tồn kho các kho của {scope}: tổng {_format_qty(quantity)}{' ' + unit if unit else ''} trên {len(rows)} kho."
    else:
        noun = pres.get("summary_noun") or "dòng dữ liệu"
        verb = pres.get("fallback_summary_verb") or "trích xuất"
        label = f"{scope}: có {total:,} {noun}" if total is not None else f"{scope}: {verb} {len(rows)} {noun}"
        if quantity is not None:
            label += f", tổng số lượng {_format_qty(quantity)}"
        if pres.get("summary_revenue") and revenue is not None:
            label += f", tổng thành tiền {revenue:,.0f} VND"
        label += "."
    blocks = [{"type": "summary", "text": label, "source_ids": source_ids}]
    if not rows:
        return blocks
    custom_labels = report.get("field_labels") if isinstance(report.get("field_labels"), dict) else {}
    columns = pres.get("columns") or _infer_columns(rows, custom_labels)
    filter_keys = pres.get("filter_keys")
    table_block = {
        "type": "table",
        "title": title,
        "columns": columns,
        "rows": [{c["key"]: _value(row.get(c["key"])) for c in columns} for row in rows],
        "total_rows": (total or len(rows)) if pres.get("summary_mode") == "warehouse_balance" else total,
        "returned_rows": len(rows),
        "has_more": has_more,
        "filters": {k: filters.get(k) for k in filter_keys} if filter_keys else filters,
        "source_ids": source_ids,
    }
    if pres.get("sort"):
        table_block["sort"] = pres["sort"]
    blocks.append(table_block)
    blocks.extend(_table_chart_block(question, rows, pres, quantity, has_more, source_ids))
    return blocks


def _configured_report_blocks(question, item, pres, report):
    if pres.get("mode") == "scalar_inventory":
        return _scalar_inventory_blocks(item)
    return _configured_table_blocks(question, item, pres, report)


def receipt_blocks(question, verified, status, *, config=None):
    """Build deterministic display blocks from config specs and verified tool results."""
    reports_by_tool = {}
    if isinstance(config, dict):
        for r in config.get("reports") or ():
            if isinstance(r, dict) and r.get("tool_name"):
                reports_by_tool[r["tool_name"]] = r
    semantic_items = [item for item in verified if item.get("tool") == "query_semantic_plan"]
    omit_semantic_summary = len(semantic_items) > 1 and status == "answered"
    blocks = []
    for item in verified:
        tool_name = str(item.get("tool") or "")
        if tool_name == "query_semantic_plan":
            blocks.extend(_semantic_blocks(question, item, include_summary=not omit_semantic_summary, config=config))
            continue
        report = reports_by_tool.get(tool_name, {})
        pres = report.get("presentation") if isinstance(report.get("presentation"), dict) else _DEFAULT_REPORT_PRESENTATIONS.get(tool_name)
        if isinstance(pres, dict):
            blocks.extend(_configured_report_blocks(question, item, pres, report))
        elif tool_name in reports_by_tool or tool_name.startswith("query_"):
            blocks.extend(_generic_lookup_blocks(item, report=report, config=config))
    if blocks and status != "answered" and any(b.get("type") == "table" for b in blocks):
        blocks.append({"type": "warning", "text": f"Câu trả lời chưa hoàn tất ({status}); các dòng trên là kết quả đã xác minh.", "source_ids": []})
    return blocks


def _generic_lookup_blocks(item, *, report=None, config=None):
    """Build a Rich UI table block for operational lookup tools that return rows."""
    tool_name = item.get("tool") or ""
    result = item.get("result") or {}
    rows = result.get("rows")
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return []
    if not isinstance(report, dict) or not report:
        report = {}
        if isinstance(config, dict):
            reports = config.get("reports") or ()
            report = next((r for r in reports if isinstance(r, dict) and r.get("tool_name") == tool_name), {})
    custom_labels = report.get("field_labels") if isinstance(report.get("field_labels"), dict) else {}
    source_ids = [s["id"] for s in result.get("sources", []) if isinstance(s, dict) and s.get("id")]
    columns = _infer_columns(rows, custom_labels)
    summary = result.get("summary") or {}
    total_rows = summary.get("total_records") if isinstance(summary.get("total_records"), int) else None
    title = report.get("title") or LOOKUP_TITLES.get(tool_name, f"Kết quả tra cứu ({tool_name})")
    return [{
        "type": "table",
        "title": title,
        "columns": columns,
        "rows": [{c["key"]: _value(row.get(c["key"])) for c in columns} for row in rows],
        "total_rows": total_rows,
        "returned_rows": len(rows),
        "has_more": bool(result.get("has_more")),
        "filters": item.get("arguments") or {},
        "source_ids": source_ids,
    }]


def _semantic_scope_suffix(applied_filters):
    """Format applied semantic filters concisely for display headers."""
    day_from = day_to = day_eq = None
    extras = []
    for f in applied_filters or ():
        if not isinstance(f, dict):
            continue
        field, op, val = f.get("field"), f.get("op"), f.get("value")
        if field == "day":
            if op == "gte":
                day_from = val
            elif op == "lte":
                day_to = val
            elif op == "eq":
                day_eq = val
        elif field and val not in (None, ""):
            label = SEMANTIC_FIELD_META.get(field, (field,))[0]
            extras.append(f"{label}={val}")
    parts = []
    if day_eq:
        parts.append(f"ngày {day_eq}")
    elif day_from and day_to:
        parts.append(f"{day_from} đến {day_to}")
    elif day_from:
        parts.append(f"từ {day_from}")
    elif day_to:
        parts.append(f"đến {day_to}")
    parts.extend(extras)
    return f" ({', '.join(parts)})" if parts else ""


_UNIT_METRIC_KEYS = frozenset({
    "quantity", "in_qty", "out_qty", "lot_qty", "ok_qty", "ng_qty",
    "planned_qty", "complete_qty", "packing_qty", "required_qty", "issued_qty",
    "used_qty", "remaining_qty", "variance_qty", "stock_qty", "return_qty",
    "transfer_qty", "pending_qty", "actual_qty", "bom_qty", "skip_qty", "schedule_qty",
})


def _semantic_chart_block(question, title, rows, columns, plan, has_more, source_ids):
    """Build an optional chart block for uniform-unit semantic aggregates."""
    if not (2 <= len(rows) <= 20):
        return None
    col_types = {c["key"]: c["type"] for c in columns}
    num_cols = [c["key"] for c in columns if c["type"] == "number"]
    if not num_cols:
        return None
    order_fields = [o.get("field") for o in (plan.get("order_by") or ()) if isinstance(o, dict)]
    metric_key = next((f for f in order_fields if f in num_cols), num_cols[0])
    if any(not isinstance(r.get(metric_key), (int, float, Decimal)) for r in rows):
        return None
    if metric_key in _UNIT_METRIC_KEYS and "unit" in rows[0]:
        if len({str(r.get("unit") or "") for r in rows}) > 1:
            return None
    if metric_key.endswith("_orig") and "currency" in rows[0]:
        if len({str(r.get("currency") or "") for r in rows}) > 1:
            return None
    dim_keys = [c["key"] for c in columns if c["type"] != "number"]
    label_dims = [k for k in dim_keys if k not in ("unit", "currency")] or dim_keys
    if not label_dims:
        return None
    pair_map = {
        "customer": "customer_name",
        "supplier": "supplier_name",
        "material": "material_name",
        "product": "product_name",
        "warehouse": "warehouse_name",
        "target_warehouse": "target_warehouse_name",
        "mold": "mold_name",
        "account": "account_name",
        "partner": "partner_name",
        "employee_code": "employee_name",
        "reason_code": "reason_name",
        "defect_code": "defect_name",
    }
    primary_dim = label_dims[0]
    name_dim = pair_map.get(primary_dim)
    if name_dim and name_dim not in col_types:
        name_dim = None
    points = []
    seen_labels = set()
    for row in rows:
        code_val = str(_value(row.get(primary_dim)) or "—")
        if name_dim and row.get(name_dim):
            lbl = f"{row[name_dim]} ({code_val})"
        else:
            lbl = code_val
        if lbl in seen_labels and len(label_dims) > 1:
            lbl = " · ".join(str(_value(row.get(k)) or "—") for k in label_dims if k != name_dim)
        seen_labels.add(lbl)
        points.append({"category": lbl, "quantity": float(row[metric_key])})
    unit = ""
    if metric_key.endswith("_vnd"):
        unit = "VND"
    elif metric_key.endswith("_pct") or metric_key == "efficiency":
        unit = "%"
    elif metric_key in ("stop_minutes", "avg_stop_minutes", "run_minutes", "net_minutes", "standard_minutes", "setup_minutes"):
        unit = "phút"
    elif metric_key in ("cycle_time", "cycle_sec"):
        unit = "giây"
    elif metric_key in ("total_shots", "warranty_shots", "remaining_warranty_shots"):
        unit = "shot"
    elif "unit" in rows[0] and len({str(r.get("unit") or "") for r in rows}) == 1:
        unit = str(rows[0].get("unit") or "")
    elif "currency" in rows[0] and metric_key.endswith("_orig") and len({str(r.get("currency") or "") for r in rows}) == 1:
        unit = str(rows[0].get("currency") or "")
    metric_label = SEMANTIC_FIELD_META.get(metric_key, (metric_key,))[0]
    x_label = SEMANTIC_FIELD_META.get(primary_dim, (primary_dim,))[0]
    is_date = col_types.get(primary_dim) == "date" and not name_dim
    vals = [p["quantity"] for p in points]
    pie_ok = (not has_more and 2 <= len(points) <= 8 and all(v >= 0 for v in vals) and sum(vals) > 0)
    wants_pie = any(t in (question or "").lower() for t in ("tỷ trọng", "ty trong", "cơ cấu", "co cau", "phần trăm", "phan tram", "biểu đồ tròn", "pie"))
    chart_type = "pie" if (wants_pie and pie_ok) else ("line" if is_date else "bar")
    return {
        "type": "chart",
        "chart_type": chart_type,
        "allowed_chart_types": ["bar", "line", *(["pie"] if pie_ok else [])],
        "title": f"{metric_label} theo {x_label.lower()}",
        "x": {"key": "category", "label": x_label, "type": "date" if is_date else "text"},
        "series": [{"key": "quantity", "label": metric_label, "unit": unit}],
        "points": points,
        "scope": f"{len(rows)} dòng đang hiển thị" if has_more else "Toàn bộ dòng trong bảng",
        "source_ids": source_ids,
    }


def _semantic_blocks(question, item, *, include_summary=True, config=None):
    """Build deterministic summary, table, and optional chart blocks for semantic plans."""
    result = item["result"]
    rows = result.get("rows", [])
    source_ids = [s["id"] for s in result.get("sources", [])]
    contract_id = result.get("contract_id") or ""
    contract = ((config.get("semantic_contracts") or {}).get(contract_id) or {}) if isinstance(config, dict) else {}
    custom_labels = contract.get("field_labels") if isinstance(contract.get("field_labels"), dict) else {}
    metric_defs = contract.get("metrics") if isinstance(contract.get("metrics"), dict) else {}
    has_more = bool(result.get("has_more"))
    res_status = result.get("status")
    try:
        from .semantic_normalizer import parse_plan_arguments
        plan = parse_plan_arguments(item.get("arguments") or {})
    except (ValueError, TypeError):
        plan = {}
    if not isinstance(plan, dict):
        plan = {}
    title = contract.get("title") or SEMANTIC_DATASET_TITLES.get(contract_id, f"Tổng hợp {contract_id or 'dữ liệu'}")
    scope_suffix = _semantic_scope_suffix(result.get("applied_filters") or plan.get("filters"))
    total_rows = result.get("total_rows") if isinstance(result.get("total_rows"), int) else None
    if not rows:
        label = f"{title}{scope_suffix}: không tìm thấy dòng phù hợp với điều kiện và quyền truy cập."
        if contract.get("notes"):
            label += f" Lưu ý dữ liệu hệ thống: {contract['notes']}"
    elif res_status == "partial" or has_more:
        total_detail = f" trên tổng {total_rows:,} dòng" if total_rows is not None else ""
        label = f"{title}{scope_suffix}: chỉ hiển thị {len(rows)} dòng đầu{total_detail}; kết quả chưa đầy đủ vì vượt giới hạn hiển thị."
    elif res_status == "missing":
        label = f"{title}{scope_suffix}: có {len(rows)} dòng nhưng chứa chỉ tiêu giá trị trống, chưa đủ căn cứ kết luận là số 0."
    else:
        totals_note = ""
        if len(rows) > 1:
            unit_single = "unit" not in rows[0] or len({str(r.get("unit") or "") for r in rows}) == 1
            curr_single = "currency" not in rows[0] or len({str(r.get("currency") or "") for r in rows}) == 1
            metric_keys = [m for m in (plan.get("metrics") or ()) if m in rows[0] and all(isinstance(r.get(m), (int, float, Decimal)) for r in rows)]
            non_summable = {"oee_pct", "availability_pct", "performance_pct", "quality_pct", "efficiency", "avg_price_vnd", "avg_stop_minutes", "cycle_time", "cycle_sec", "cavity", "total_shots", "warranty_shots", "remaining_warranty_shots"}
            sum_parts = []
            for m in metric_keys[:3]:
                mdef = metric_defs.get(m) if isinstance(metric_defs.get(m), dict) else {}
                agg = mdef.get("aggregate")
                if agg in ("avg", "min", "max") or mdef.get("non_summable") or m in non_summable:
                    continue
                if (mdef.get("unit_dimension") == "unit" or m in _UNIT_METRIC_KEYS) and not unit_single:
                    continue
                if (mdef.get("unit_dimension") == "currency" or m.endswith("_orig")) and not curr_single:
                    continue
                total_val = sum(float(r[m]) for r in rows)
                lbl = custom_labels.get(m) or SEMANTIC_FIELD_META.get(m, (m,))[0]
                fmt = f"{int(total_val):,}" if float(total_val).is_integer() else f"{total_val:,.2f}"
                unit_lbl = f" {rows[0]['unit']}" if ("unit" in rows[0] and unit_single and (mdef.get("unit_dimension") == "unit" or m in _UNIT_METRIC_KEYS)) else ""
                sum_parts.append(f"{lbl}: {fmt}{unit_lbl}")
            if sum_parts:
                totals_note = " Tổng cộng: " + "; ".join(sum_parts) + "."
        label = f"{title}{scope_suffix}: tổng hợp được {len(rows)} dòng dữ liệu đã xác minh.{totals_note}"
    out = [{"type": "summary", "text": label, "source_ids": source_ids}] if include_summary else []
    if not rows:
        return out
    ordered_keys = []
    for k in [*(plan.get("dimensions") or ()), *(plan.get("metrics") or ())]:
        if k in rows[0] and k not in ordered_keys:
            ordered_keys.append(k)
    for k in rows[0]:
        if k not in ordered_keys:
            ordered_keys.append(k)
    columns = []
    for key in ordered_keys:
        if key in custom_labels:
            col_type = "date" if (key == "day" or key.endswith("_date") or key in ("valid_from", "valid_to")) else ("number" if isinstance(rows[0].get(key), (int, float, Decimal)) else "text")
            lbl = custom_labels[key]
        elif key in SEMANTIC_FIELD_META:
            lbl, col_type = SEMANTIC_FIELD_META[key]
        else:
            col_type = "date" if (key == "day" or key.endswith("_date") or key in ("valid_from", "valid_to")) else ("number" if isinstance(rows[0].get(key), (int, float, Decimal)) else "text")
            lbl = get_column_caption(key)
        columns.append({"key": key, "label": lbl, "type": col_type})
    out.append({
        "type": "table",
        "title": title,
        "columns": columns,
        "rows": [{c["key"]: _value(row.get(c["key"])) for c in columns} for row in rows],
        "total_rows": total_rows,
        "returned_rows": len(rows),
        "has_more": has_more,
        "filters": result.get("applied_filters") or [],
        "source_ids": source_ids,
    })
    chart = _semantic_chart_block(question, title, rows, columns, plan, has_more, source_ids)
    if chart:
        out.append(chart)
    return out


def render_markdown(blocks):
    """Open WebUI can display the same blocks as a GFM table without HTML."""
    parts = []
    for block in blocks:
        kind = block["type"]
        if kind == "summary":
            parts.append(block["text"])
        elif kind == "warning":
            parts.append("Lưu ý: " + block["text"])
        elif kind == "table":
            columns = block["columns"]
            lines = ["| " + " | ".join(c["label"] for c in columns) + " |",
                     "| " + " | ".join("---:" if c["type"] == "number" else "---" for c in columns) + " |"]
            lines += ["| " + " | ".join(_cell(row.get(c["key"])) for c in columns) + " |" for row in block["rows"]]
            parts.append("\n".join(lines))
        elif kind == "chart":
            # Portable bar chart in GFM, with the numeric value beside each bar.
            points = block["points"]
            top = max(abs(p["quantity"]) for p in points) or 1
            unit = block["series"][0]["unit"]
            lines = [f"{block['title']} ({unit or 'đơn vị chưa xác định'}; {block['scope']})",
                     f"| {block['x']['label']} | Số lượng | Biểu đồ |", "| --- | ---: | --- |"]
            for point in points:
                width = round(abs(point["quantity"]) / top * 20)
                lines.append(f"| {_cell(point['category'])} | {point['quantity']:g} | {'▮' * width} |")
            lines.append(f"Chú giải: ▮ = {block['series'][0]['label']} ({unit or 'đơn vị chưa xác định'}).")
            parts.append("\n".join(lines))
    return "\n\n".join(parts)
