"""Explicit allowlist retrieval and parameterized, scoped report execution."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import date
from pathlib import Path
from .validator import validate_inventory_balance_result


def tokens(value):
    value = unicodedata.normalize("NFD", value.lower().replace("đ", "d"))
    return set(re.findall(r"[a-z0-9_]+", "".join(c for c in value if not unicodedata.combining(c))))


def spec(name, description, fields, optional=()):
    props = {k: {"type": "string"} for k in list(fields) + list(optional)}
    return {"type": "function", "function": {"name": name, "description": description,
            "parameters": {"type": "object", "properties": props,
                           "required": list(fields), "additionalProperties": False}}}


class ReportBackend:
    specs = [spec("search_knowledge", "Tìm tri thức nghiệp vụ có nguồn và trạng thái hiệu lực", ["query"]),
             spec("search_schema", "Tìm báo cáo và bảng cho phép theo câu hỏi", ["query"]),
             spec("describe_table", "Mô tả schema của một báo cáo cho phép", ["report_id"]),
             spec("query_allowed_records",
                  "Đọc chi tiết và tổng hợp dòng phiếu xuất kho bán hàng (ph81/ct81). BẮT BUỘC có mã vật tư (material) và khoảng ngày ISO (tối đa 31 ngày). "
                  "Chỉ dùng cho xuất kho bán hàng; KHÔNG dùng cho tồn kho, BOM, bảng giá/MOQ, QC, đơn hàng hay master khách hàng. "
                  "Sử dụng trường summary trong kết quả để lấy tổng số lượng và số dòng toàn kỳ.",
                  ["report_id", "material", "date_from", "date_to"]),
             spec("query_price_list",
                  "Tra cứu bảng giá, giá bán hiện tại và MOQ (số lượng đặt tối thiểu sl_min) theo mã vật tư (material) và ngày tham chiếu (date_as_of định dạng YYYY-MM-DD).",
                  ["material", "date_as_of"]),
             spec("query_bom_structure",
                  "Tra cứu cấu trúc sản phẩm BOM, định mức nguyên vật liệu và loại nhựa theo mã sản phẩm mẹ (material) và ngày tham chiếu (date_as_of định dạng YYYY-MM-DD).",
                  ["material", "date_as_of"]),
             spec("query_customer_info",
                  "Tra cứu danh mục khách hàng theo mã khách hàng hoặc tên khách hàng (query_text).",
                  ["query_text"]),
             spec("query_material_customer",
                  "Tra khách hàng ĐƯỢC KHAI BÁO trên mã hàng/vật tư (material) từ dmvt.ma_kh. Dùng khi hỏi mã hàng thuộc khách nào; không dùng query_customer_info.",
                  ["material"]),
             spec("query_inventory_balance",
                  "Tra cứu số lượng tồn kho sổ sách của mã vật tư (material) tính đến ngày tham chiếu (date_as_of định dạng YYYY-MM-DD).",
                  ["material", "date_as_of"]),
             spec("query_inventory_by_warehouse",
                  "Tra tồn kho sổ sách của mã vật tư (material) THEO TỪNG KHO tại ngày tham chiếu (date_as_of). Dùng khi người dùng hỏi 'ở từng kho', 'theo kho', hoặc 'kho nào bao nhiêu'.",
                  ["material", "date_as_of"]),
             spec("query_receipt_lines",
                  "Tra cứu dòng phiếu nhập kho và điều chuyển theo mã vật tư (material) và khoảng ngày (date_from, date_to). Trả về ngày nhập, số lượng nhập, người nhập và kho xuất.",
                  ["material", "date_from", "date_to"]),
             spec("query_forecast_po",
                  "Tra cứu dữ liệu kế hoạch sản xuất PO và dự báo FCST theo mã vật tư (material) từ bảng mfkhsx_po_fc.",
                  ["material"], optional=["date_as_of"]),
             spec("query_packaging_spec",
                  "Tra cứu quy cách đóng gói chi tiết của mã vật tư (material) từ danh mục dmvt (packs0, ma_thung, ma_khay, số lượng vật tư/khay, pallet).",
                  ["material"], optional=["date_as_of"]),
             spec("query_mold_profile",
                  "Tra cứu hồ sơ khuôn, tổng số shot dập lũy kế (tong_so_shot) và số shot bảo hành định mức (so_shot_bh) theo mã khuôn (mold) và mã sản phẩm (material).",
                  ["mold", "material"], optional=["date_as_of"]),
             spec("query_mold_label_stock",
                  "Tra cứu tồn kho theo khuôn và die_no (V1, V2...) từ tem hoạt động intem_log theo mã vật tư (material).",
                  ["material"], optional=["date_as_of"]),
             spec("query_sales_orders",
                  "Tra cứu đơn hàng bán (SO) trong kỳ theo mã khách hàng (customer: ví dụ KH0015) và khoảng ngày (date_from, date_to). Dùng để lấy data đơn hàng hoặc kiểm tra mã chưa link giá chuẩn (gia_chuan = 0).",
                  ["customer", "date_from", "date_to"]),
             spec("query_sales_order_price_gaps",
                  "Liệt kê TOÀN BỘ mã hàng là ứng viên thiếu liên kết giá chuẩn trong đơn hàng bán của khách (customer) và khoảng ngày; gia_chuan NULL/0 cần xác minh nghiệp vụ.",
                  ["customer", "date_from", "date_to"]),
             spec("query_delivery_order",
                  "Tra cứu trạng thái lệnh giao hàng (delivery_code: số chứng từ TO2, ví dụ 001-2610-001811) và thời điểm tạo lập.",
                  ["delivery_code"]),
             spec("query_qc_status",
                  "Tra cứu tồn kho thành phẩm theo trạng thái kiểm tra chất lượng tem QC (status_qc) theo mã vật tư (material).",
                  ["material"], optional=["date_as_of"]),
             spec("query_replacement_orders",
                  "Tra cứu lệnh giao hàng giao bù NG (mã giao dịch 10) theo mã vật tư (material) và khoảng ngày (date_from, date_to).",
                  ["material", "date_from", "date_to"])]
    names = {s["function"]["name"] for s in specs}

    def __init__(self, root, config, grants, db):
        self.root = Path(root).resolve()
        self.config, self.grants, self.db = config, grants, db
        self.reports = {r["id"]: r for r in config["reports"]}

    def grant(self, user):
        # user is injected by the server, not accepted in tool arguments.
        value = self.grants.get(str(user.get("id", "")), {}) if isinstance(user, dict) else {}
        if not isinstance(value, dict) or type(value.get("erp_user_id")) is not int or value["erp_user_id"] <= 0:
            return {}
        return value

    def authorized(self, user):
        return bool(self.grant(user).get("reports"))

    def allowed(self, user):
        return {k: v for k, v in self.reports.items() if k in self.grant(user).get("reports", [])}

    def read(self, relative):
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root) or path.stat().st_size > 200000:
            raise ValueError("invalid configured asset")
        return path.read_text()

    def schema(self, report):
        return {k: report[k] for k in ("id", "title", "tables", "join", "fields", "validation")}

    def retrieve(self, query, user):
        terms, allowed = tokens(query), self.allowed(user)
        schemas = sorted(allowed.values(), key=lambda r: -len(terms & tokens(json.dumps(r, ensure_ascii=False))))
        schemas = [self.schema(r) for r in schemas if terms & tokens(json.dumps(r, ensure_ascii=False))][:3]
        matches = []
        for doc in self.config["knowledge"]:
            if doc["report_id"] not in allowed:
                continue
            body = self.read(doc["path"])
            revision = hashlib.sha256(body.encode()).hexdigest()[:16]
            for i, chunk in enumerate(re.split(r"(?m)(?=^## )", body)):
                score = len(terms & tokens(chunk))
                if score:
                    source = dict(doc, id=f"knowledge:{revision}:{i}", revision=revision,
                                  section=chunk.splitlines()[0], excerpt=chunk[:1800])
                    matches.append((score, source))
        matches.sort(key=lambda x: (x[1]["status"] == "current", x[0]), reverse=True)
        selected = [s for _, s in matches[:3]]
        # Metadata declares known conflicts. Never infer that newest means correct.
        conflicts = sorted({s["conflict_group"] for _, s in matches if s.get("conflict_group")})
        return {"schemas": schemas, "sources": selected, "conflicts": conflicts}

    def validate(self, name, args):
        param_def = next(s["function"]["parameters"] for s in self.specs if s["function"]["name"] == name)
        fields, all_props = param_def["required"], set(param_def["properties"])
        if not isinstance(args, dict) or not set(fields).issubset(set(args)) or not set(args).issubset(all_props):
            raise ValueError("arguments")
        if any(not isinstance(v, str) or not v.strip() or len(v) > 500 for v in args.values()):
            raise ValueError("arguments")
        if "date_as_of" in args:
            date.fromisoformat(args["date_as_of"])
        if name in ("query_allowed_records", "query_receipt_lines", "query_replacement_orders"):
            start, end = date.fromisoformat(args["date_from"]), date.fromisoformat(args["date_to"])
            if not 0 <= (end-start).days <= 30 or not re.fullmatch(r"[\w./-]{1,64}", args["material"]):
                raise ValueError("filters")
        elif name in ("query_sales_orders", "query_sales_order_price_gaps"):
            start, end = date.fromisoformat(args["date_from"]), date.fromisoformat(args["date_to"])
            if not 0 <= (end-start).days <= 30 or not re.fullmatch(r"[\w./-]{1,64}", args["customer"]):
                raise ValueError("filters")
        elif name in ("query_price_list", "query_bom_structure", "query_inventory_balance", "query_inventory_by_warehouse"):
            date.fromisoformat(args["date_as_of"])
            if not re.fullmatch(r"[\w./-]{1,64}", args["material"]):
                raise ValueError("filters")
        elif name in ("query_forecast_po", "query_packaging_spec", "query_mold_label_stock", "query_qc_status", "query_material_customer"):
            if not re.fullmatch(r"[\w./-]{1,64}", args["material"]):
                raise ValueError("filters")
        elif name == "query_mold_profile":
            if not re.fullmatch(r"[\w./-]{1,64}", args["mold"]) or not re.fullmatch(r"[\w./-]{1,64}", args["material"]):
                raise ValueError("filters")
        elif name == "query_delivery_order":
            if not re.fullmatch(r"[\w./-]{1,64}", args["delivery_code"]):
                raise ValueError("filters")
        elif name == "query_customer_info":
            if not args["query_text"].strip() or len(args["query_text"]) > 128:
                raise ValueError("filters")

    async def execute(self, name, args, user, limits):
        if not self.authorized(user):
            return {"error": "forbidden"}
        self.validate(name, args)
        if name in ("search_knowledge", "search_schema"):
            result = self.retrieve(args["query"], user)
            if name == "search_schema":
                result["sources"] = [self.report_source(self.reports[s["id"]]) for s in result["schemas"]]
            return result
        tool_report_map = {
            "query_allowed_records": args.get("report_id"),
            "query_price_list": "price_list",
            "query_bom_structure": "product_structure",
            "query_customer_info": "customer_master",
            "query_material_customer": "material_customer",
            "query_inventory_balance": "inventory_balance",
            "query_inventory_by_warehouse": "inventory_by_warehouse",
            "query_receipt_lines": "receipt_lines",
            "query_forecast_po": "forecast_po",
            "query_packaging_spec": "packaging_spec",
            "query_mold_profile": "mold_profile",
            "query_mold_label_stock": "mold_label_stock",
            "query_sales_orders": "sales_orders",
            "query_sales_order_price_gaps": "sales_order_price_gaps",
            "query_delivery_order": "delivery_order",
            "query_qc_status": "qc_label_status",
            "query_replacement_orders": "replacement_orders",
        }
        report_id = tool_report_map.get(name, args.get("report_id"))
        report = self.allowed(user).get(report_id)
        if not report:
            return {"error": "forbidden_report"}
        source = self.report_source(report)
        if name == "describe_table":
            return {"schema": self.schema(report), "sources": [source]}
        # SQL/identifiers never come from the model. Each report declares its binding order.
        bindings = dict(args, user_id=self.grant(user)["erp_user_id"], row_limit=limits.rows + 1)
        sql = self.read(report["query_file"])
        rows = await self.db(sql, tuple(bindings.get(k, '') if k not in ('user_id', 'row_limit') else bindings[k] for k in report["parameters"]), limits)
        has_more = len(rows) > limits.rows
        rows = rows[:limits.rows]

        summary = {}
        if rows:
            first = rows[0]
            if "total_lines" in first and first["total_lines"] is not None:
                summary["total_records"] = int(first["total_lines"])
            if "total_quantity" in first and first["total_quantity"] is not None:
                summary["total_quantity"] = float(first["total_quantity"])
            if "total_revenue" in first and first["total_revenue"] is not None:
                summary["total_revenue"] = float(first["total_revenue"])
        elif not has_more:
            summary["total_records"] = 0
            if name != "query_inventory_balance":
                summary["total_quantity"] = 0.0

        # Only reviewed fields leave the adapter. No URL generation in this slice.
        rows = [{k: v for k, v in row.items() if k in report["fields"]} for row in rows]
        if name == "query_inventory_balance" and rows:
            error = ("INVENTORY_RESULT_TRUNCATED" if has_more else
                     validate_inventory_balance_result(args["material"], rows))
            if error:
                return {"error": "invalid_result", "error_code": error}
        if name == "query_sales_orders" and len(rows) > 5:
            rows = rows[:5]
            has_more = True
        source_key = [report_id, self.grant(user)["erp_user_id"], args]
        source = dict(source, id="records:" + hashlib.sha256(json.dumps(source_key, sort_keys=True).encode()).hexdigest()[:16])
        result = {"rows": rows, "returned_rows": len(rows), "has_more": has_more,
                  "sources": [source], "validation": report["validation"], "summary": summary}
        while rows and len(json.dumps(result, default=str, ensure_ascii=False)) > limits.result_chars:
            rows.pop()
            result.update(returned_rows=len(rows), has_more=True)
        return result

    @staticmethod
    def report_source(report):
        return {"id": "schema:" + report["id"], "path": report["manifest"], "title": report["title"],
                "tables": report["tables"], "validation": report["validation"]}
