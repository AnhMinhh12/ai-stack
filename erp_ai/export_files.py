"""Create downloadable office files from verified ERP display blocks."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from io import BytesIO
from math import isfinite
from pathlib import Path
import re
import subprocess
import tempfile


FILE_TYPES = {
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
}


def requested_formats(question: str) -> tuple[str, ...]:
    """Offer Excel immediately and let the user request Word/PDF by clicking."""
    return ("xlsx", "docx", "pdf")


def clean_numeric_str(value):
    """Format numeric values without trailing redundant zeros."""
    if isinstance(value, Decimal):
        s = format(value, "f")
        if "." in s:
            s = s.rstrip("0").rstrip(".")
        return s or "0"
    if isinstance(value, float):
        s = f"{value:.10f}".rstrip("0").rstrip(".")
        return s or "0"
    if isinstance(value, str) and re.match(r"^-?\d+\.\d+$", value):
        s = value.rstrip("0").rstrip(".")
        return s or "0"
    return value


def blocks_from_rows(payload):
    """Adapt a single verified ERP tool result to the shared table format."""
    if not isinstance(payload, dict) or payload.get("status") not in (None, "success"):
        return []
    rows = payload.get("rows") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows or not all(isinstance(row, dict) for row in rows):
        return []
    raw_keys = list(rows[0])
    if not raw_keys or any(set(row) != set(raw_keys) for row in rows):
        return []
    keys = [k for k in raw_keys if k not in ("total", "total_lines")]
    if not keys:
        keys = raw_keys
    cleaned_rows = [
        {k: clean_numeric_str(row.get(k)) for k in keys}
        for row in rows
    ]
    requested = payload.get("requested_columns") or []
    labels = {
        item.get("field"): item.get("label")
        for item in requested if isinstance(item, dict) and item.get("field")
    }
    field_labels = {
        "ma_vt": "Mã VT", "ten_vt": "Tên vật tư", "dvt": "ĐVT",
        "so_luong": "Số lượng", "doanh_thu": "Doanh thu", "so_ct": "Số CT",
        "ngay_ct": "Ngày CT", "ma_kho": "Mã kho", "ten_kho": "Tên kho",
        "sl_nhap": "SL nhập", "sl_xuat": "SL xuất", "tien2": "Tiền hàng",
        "nguoi_lap": "Người lập", "gia": "Đơn giá", "gia2": "Đơn giá",
    }
    columns = [{"key": key, "label": labels.get(key) or field_labels.get(key) or key, "type": "text"} for key in keys]
    total = payload.get("total_rows")
    if not isinstance(total, int):
        total = payload.get("row_count")
    report = payload.get("report") or {}
    title = report.get("title") if isinstance(report, dict) else None
    blocks = [{
        "type": "table", "title": title or "Kết quả ERP", "columns": columns, "rows": cleaned_rows,
        "total_rows": total, "has_more": bool(payload.get("has_more") or payload.get("truncated")),
    }]
    summary = payload.get("summary")
    if isinstance(summary, dict) and summary:
        labels = {
            "total_records": "Tổng số dòng", "total_quantity": "Tổng số lượng",
            "tong_so_luong": "Tổng số lượng", "tong_doanh_thu": "Tổng doanh thu",
            "total_revenue": "Tổng doanh thu", "so_luong_ton": "Số lượng tồn",
            "dvt": "Đơn vị tính",
        }
        details = ", ".join(
            f"{labels.get(key, key)}: {clean_numeric_str(value)}" for key, value in summary.items()
            if isinstance(value, (str, int, float, Decimal)) and not isinstance(value, bool)
        )
        if details:
            blocks.insert(0, {"type": "summary", "text": f"Thống kê ERP — {details}"})
    if {"ngay_ct", "sl_nhap", "dvt"}.issubset(keys):
        units = {str(row.get("dvt") or "") for row in rows}
        grouped = {}
        for row in rows:
            try:
                value = float(row["sl_nhap"])
            except (TypeError, ValueError):
                grouped = {}
                break
            if not isfinite(value):
                grouped = {}
                break
            day = str(row.get("ngay_ct") or "")
            grouped[day] = grouped.get(day, 0) + value
        if len(units) == 1 and len(grouped) > 1:
            partial = blocks[-1]["has_more"] or (isinstance(total, int) and total > len(rows))
            blocks.append({
                "type": "chart", "chart_type": "line", "allowed_chart_types": ["bar", "line"],
                "title": "Số lượng nhập theo ngày", "x": {"label": "Ngày nhập"},
                "series": [{"label": "Số lượng nhập", "unit": next(iter(units))}],
                "points": [{"category": day, "quantity": value} for day, value in sorted(grouped.items())],
                "scope": f"{len(rows)} dòng đang hiển thị" if partial else "Toàn bộ dòng trong bảng",
            })
    return blocks


def _tables(blocks):
    return [block for block in blocks if block.get("type") == "table" and block.get("columns")]


def _as_cell(value):
    if value is None:
        return ""
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value if isinstance(value, (str, int, float, bool)) else str(value)


def _scope_note(block):
    count = len(block.get("rows") or [])
    total = block.get("total_rows")
    if block.get("has_more") or (isinstance(total, int) and total > count):
        return f"Chỉ xuất {count} dòng đã trả về; báo cáo có thêm dòng chưa được xuất."
    return f"Số dòng xuất: {count}."


def _xlsx(blocks):
    from openpyxl import Workbook
    from openpyxl.styles import Font
    from openpyxl.utils import get_column_letter

    book = Workbook()
    book.remove(book.active)
    for index, block in enumerate(_tables(blocks), start=1):
        title = re.sub(r"[\\/*?:\[\]]", " ", str(block.get("title") or "Báo cáo"))[:25]
        sheet = book.create_sheet(f"{index} {title}"[:31])
        columns = block["columns"]
        sheet.append([str(column.get("label") or column["key"]) for column in columns])
        for cell in sheet[1]:
            cell.font = Font(bold=True)
        for row in block.get("rows") or []:
            sheet.append([_as_cell(row.get(column["key"])) for column in columns])
            # ERP text is data, even when it starts with an Excel formula marker.
            for cell in sheet[sheet.max_row]:
                if isinstance(cell.value, str):
                    cell.data_type = "s"
        sheet.freeze_panes = "A2"
        sheet.auto_filter.ref = f"A1:{get_column_letter(len(columns))}{max(sheet.max_row, 1)}"
        for column_index, column in enumerate(columns, start=1):
            width = max(len(str(column.get("label") or column["key"])), *(len(str(_as_cell(row.get(column["key"])))) for row in block.get("rows") or []))
            sheet.column_dimensions[get_column_letter(column_index)].width = min(max(width + 2, 12), 45)
        sheet.append([])
        sheet.append([_scope_note(block)])
    data = BytesIO()
    book.save(data)
    return data.getvalue()


def _docx(blocks):
    from docx import Document

    document = Document()
    document.add_heading("Kết quả tra cứu ERP", 0)
    for block in blocks:
        if block.get("type") in ("summary", "warning"):
            document.add_paragraph(str(block.get("text") or ""))
        if block.get("type") != "table" or not block.get("columns"):
            continue
        document.add_heading(str(block.get("title") or "Báo cáo"), level=1)
        columns = block.get("columns") or []
        table = document.add_table(rows=1, cols=len(columns))
        table.style = "Table Grid"
        for cell, column in zip(table.rows[0].cells, columns):
            cell.text = str(column.get("label") or column["key"])
        for row in block.get("rows") or []:
            for cell, column in zip(table.add_row().cells, columns):
                cell.text = str(_as_cell(row.get(column["key"])))
        document.add_paragraph(_scope_note(block))
    data = BytesIO()
    document.save(data)
    return data.getvalue()


def _pdf(docx_data):
    with tempfile.TemporaryDirectory(prefix="erp-export-") as temp_dir:
        source = Path(temp_dir) / "bao-cao-erp.docx"
        source.write_bytes(docx_data)
        subprocess.run(
            ["libreoffice", "-env:UserInstallation=file://" + temp_dir + "/profile",
             "--headless", "--convert-to", "pdf:writer_pdf_Export", "--outdir", temp_dir, str(source)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30,
        )
        output = source.with_suffix(".pdf")
        if not output.is_file():
            raise RuntimeError("PDF conversion did not create a file")
        return output.read_bytes()


def build_downloads(blocks, formats):
    """Return filename, MIME type and bytes; never use model prose as source data."""
    if not _tables(blocks):
        return []
    output = []
    docx_data = None
    for format_name in formats:
        if format_name not in FILE_TYPES:
            continue
        if format_name == "xlsx":
            data = _xlsx(blocks)
        else:
            if docx_data is None:
                docx_data = _docx(blocks)
            data = docx_data if format_name == "docx" else _pdf(docx_data)
        output.append({"name": f"bao-cao-erp.{format_name}", "mime": FILE_TYPES[format_name], "data": data})
    return output
