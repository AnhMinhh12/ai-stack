"""Deterministic ERP display blocks built only from verified tool results."""
from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from decimal import Decimal
from html import escape


RECEIPT_COLUMNS = [
    {"key": "ngay_ct", "label": "Ngày nhập", "type": "date"},
    {"key": "so_ct", "label": "Số chứng từ", "type": "text"},
    {"key": "ma_kho", "label": "Kho nhận", "type": "text"},
    {"key": "kho_xuat", "label": "Kho xuất chuyển", "type": "text"},
    {"key": "sl_nhap", "label": "Số lượng", "type": "number"},
    {"key": "dvt", "label": "Đơn vị", "type": "text"},
    {"key": "nguoi_nhap", "label": "Người nhập", "type": "text"},
]


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


def receipt_blocks(question, verified, status):
    """One table per successful receipt query; never mix different filters."""
    blocks = []
    receipt_materials = {item.get("arguments", {}).get("material") for item in verified
                         if item.get("tool") == "query_receipt_lines"}
    for item in verified:
        if item.get("tool") != "query_inventory_balance" or item.get("arguments", {}).get("material") not in receipt_materials:
            continue
        result = item["result"]
        rows = result.get("rows", [])
        material = item["arguments"]["material"]
        date_as_of = item["arguments"].get("date_as_of", "?")
        if not rows:
            label = f"Không tìm thấy tồn kho sổ sách của mã {material} tính đến {date_as_of}."
        elif len(rows) == 1 and rows[0].get("so_luong_ton") is not None:
            quantity = _value(rows[0]["so_luong_ton"])
            unit = rows[0].get("dvt") or ""
            label = f"Tồn kho sổ sách của mã {material} tính đến {date_as_of}: {quantity:g}{' ' + unit if unit else ''}."
        else:
            label = f"Tồn kho sổ sách của mã {material} tính đến {date_as_of}: có {len(rows)} dòng dữ liệu; chưa có tổng hợp đáng tin cậy."
        blocks.append({"type": "summary", "text": label,
                       "source_ids": [s["id"] for s in result.get("sources", [])]})
    for item in verified:
        if item.get("tool") != "query_receipt_lines":
            continue
        result = item["result"]
        rows = result.get("rows", [])
        summary = result.get("summary", {})
        source_ids = [s["id"] for s in result.get("sources", [])]
        filters = item.get("arguments", {})
        scope = f"mã {filters.get('material', '?')}, {filters.get('date_from', '?')} đến {filters.get('date_to', '?')}"
        total = summary.get("total_records")
        quantity = summary.get("total_quantity")
        has_more = bool(result.get("has_more"))
        if not rows:
            label = f"Không có giao dịch nhập kho cho {scope}." if total == 0 else f"Chưa có dòng dữ liệu cho {scope}."
        else:
            label = f"{scope}: có {total} dòng nhập kho" if total is not None else f"{scope}: đã nhận {len(rows)} dòng nhập kho"
            if quantity is not None:
                label += f", tổng số lượng {quantity:g}"
            label += "."
        blocks.append({"type": "summary", "text": label, "source_ids": source_ids})
        if rows:
            blocks.append({
                "type": "table", "title": "Lịch sử nhập kho", "columns": RECEIPT_COLUMNS,
                "rows": [{c["key"]: _value(row.get(c["key"])) for c in RECEIPT_COLUMNS} for row in rows],
                "total_rows": total, "returned_rows": len(rows), "has_more": has_more,
                "filters": {k: filters.get(k) for k in ("material", "date_from", "date_to")},
                "sort": [{"key": "ngay_ct", "direction": "desc"}, {"key": "so_ct", "direction": "desc"}],
                "source_ids": source_ids,
            })
        if has_more:
            blocks.append({"type": "warning", "text": f"Bảng mới hiển thị {len(rows)} dòng; tổng và số lượng lấy từ toàn bộ kết quả truy vấn.", "source_ids": source_ids})
        # Choose the visual deterministically from verified data, without an
        # extra model round. A partial result is always labelled as such.
        units = {str(row.get("dvt") or "") for row in rows}
        if rows and len(units) == 1:
            days = {str(_value(row.get("ngay_ct"))) for row in rows}
            lowered = question.lower()
            wants_share = any(term in lowered for term in ("tỷ trọng", "ty trong", "cơ cấu", "co cau", "phần trăm", "phan tram", "biểu đồ tròn", "bieu do tron", "pie"))
            wants_warehouse = any(term in lowered for term in ("biểu đồ theo kho", "bieu do theo kho", "theo từng kho", "theo tung kho", "so sánh các kho", "so sanh cac kho"))
            if wants_share or wants_warehouse or len(days) == 1:
                key, x_label = "ma_kho", "Kho nhận"
            else:
                key, x_label = "ngay_ct", "Ngày nhập"
            grouped = defaultdict(float)
            for row in rows:
                label = str(_value(row.get(key)) or "")
                try:
                    grouped[label] += float(row["sl_nhap"])
                except (TypeError, ValueError):
                    grouped.clear()
                    break
            matches_total = has_more or quantity is None or abs(sum(grouped.values()) - quantity) < 1e-6
            if len(grouped) > 1 and matches_total:
                chart_scope = f"{len(rows)} dòng đang hiển thị" if has_more else "Toàn bộ dòng trong bảng"
                can_pie = (wants_share and not has_more and key == "ma_kho"
                           and 2 <= len(grouped) <= 8 and all(value >= 0 for value in grouped.values())
                           and sum(grouped.values()) > 0 and quantity is not None)
                pie_available = (not has_more and 2 <= len(grouped) <= 8
                                 and all(value >= 0 for value in grouped.values())
                                 and sum(grouped.values()) > 0 and quantity is not None)
                chart_type = "pie" if can_pie else "line" if key == "ngay_ct" else "bar"
                blocks.append({
                    "type": "chart", "chart_type": chart_type,
                    "allowed_chart_types": ["bar", "line", *(["pie"] if pie_available else [])],
                    "title": ("Tỷ trọng số lượng nhập theo kho nhận" if can_pie else f"Số lượng nhập theo {x_label.lower()}"),
                    "x": {"key": "category", "label": x_label, "type": "date" if key == "ngay_ct" else "text"},
                    "series": [{"key": "quantity", "label": "Số lượng nhập", "unit": next(iter(units))}],
                    "points": [{"category": label, "quantity": value} for label, value in sorted(grouped.items())],
                    "scope": chart_scope, "source_ids": source_ids,
                })
            if wants_share and has_more:
                blocks.append({"type": "warning", "text": "Chưa vẽ biểu đồ tròn vì bảng chỉ có một phần giao dịch; biểu đồ so sánh (nếu có) chỉ dùng các dòng đang hiển thị.", "source_ids": source_ids})
    if blocks and status != "answered":
        blocks.append({"type": "warning", "text": f"Câu trả lời chưa hoàn tất ({status}); các dòng trên là kết quả đã xác minh.", "source_ids": []})
    return blocks


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
