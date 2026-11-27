"""Explicit allowlist retrieval and parameterized, scoped report execution."""
from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from datetime import date
from pathlib import Path
from typing import Any
from .validator import validate_inventory_balance_result
from .context_hints import _norm as _norm_hint_text, extract_context_hints, score_datasets
from .entities import extract_entities
from .semantic_executor import execute_joined_plan, execute_plan
from .semantic_model import load_erp_config
from .semantic_normalizer import normalize_joined_plan, normalize_semantic_plan, parse_plan_arguments
from .semantic_query import PlanError, _VN_DST, _VN_SRC, identifier
from .semantic_retriever import has_word_cue, normalize_text, rank_datasets


def tokens(value):
    value = unicodedata.normalize("NFD", value.lower().replace("đ", "d"))
    return set(re.findall(r"[a-z0-9_]+", "".join(c for c in value if not unicodedata.combining(c))))


def spec(name, description, fields, optional=()):
    props = {k: {"type": "string"} for k in list(fields) + list(optional)}
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": props,
                "required": list(fields),
                "additionalProperties": False,
            },
        },
    }


STRUCTURED_SEMANTIC_SPEC = {
    "type": "function",
    "function": {
        "name": "query_semantic_plan",
        "description": (
            "Chạy truy vấn tổng hợp/thống kê/xếp hạng trên tập dữ liệu semantic đã duyệt. "
            "Truyền trực tiếp các trường dataset, dimensions, metrics, filters, order_by, limit."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "dataset": {"type": "string"},
                "dimensions": {"type": "array", "items": {"type": "string"}},
                "metrics": {"type": "array", "items": {"type": "string"}},
                "filters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string"},
                            "op": {"type": "string", "enum": ["eq", "gte", "lte", "contains", "in"]},
                            "value": {"description": "Giá trị lọc (với op='in', dùng chuỗi ngăn cách bởi dấu phẩy hoặc mảng)."},
                        },
                        "required": ["field", "op", "value"],
                    },
                },
                "order_by": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string"},
                            "direction": {"type": "string", "enum": ["asc", "desc"]},
                        },
                        "required": ["field", "direction"],
                    },
                },
                "limit": {"type": "integer"},
            },
            "required": ["dataset", "metrics"],
            "additionalProperties": False,
        },
    },
}


def _semantic_leg_schema() -> dict:
    return {
        "type": "object",
        "properties": {
            "dataset": {"type": "string"},
            "dimensions": {"type": "array", "items": {"type": "string"}},
            "metrics": {"type": "array", "items": {"type": "string"}},
            "filters": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string"},
                        "op": {"type": "string", "enum": ["eq", "gte", "lte", "contains", "in"]},
                        "value": {"description": "Giá trị lọc (với op='in', dùng chuỗi ngăn cách bởi dấu phẩy hoặc mảng)."},
                    },
                    "required": ["field", "op", "value"],
                },
            },
            "order_by": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string"},
                        "direction": {"type": "string", "enum": ["asc", "desc"]},
                    },
                    "required": ["field", "direction"],
                },
            },
            "limit": {"type": "integer"},
        },
        "required": ["dataset", "metrics"],
        "additionalProperties": False,
    }


STRUCTURED_SEMANTIC_JOIN_SPEC = {
    "type": "function",
    "function": {
        "name": "query_semantic_join",
        "description": (
            "Ghép nối an toàn 2 hoặc 3 tập dữ liệu semantic có chung khóa thực thể trong `available_joins` "
            "(tổng hợp từng vế trước rồi nối theo `join_on`, tránh nhân bản dòng). "
            "Dùng khi câu hỏi đòi hỏi kết hợp chỉ tiêu từ 2-3 dataset (truyền vế thứ 3 vào `extra_legs` nếu cần)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "left": _semantic_leg_schema(),
                "right": _semantic_leg_schema(),
                "extra_legs": {
                    "type": "array",
                    "maxItems": 1,
                    "items": _semantic_leg_schema(),
                    "description": "Tùy chọn tối đa 1 tập dữ liệu thứ 3 có chung khóa `join_on` để đối chiếu 3 chiều.",
                },
                "join_on": {"type": "string"},
                "join_type": {"type": "string", "enum": ["left", "inner"]},
                "order_by": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string"},
                            "direction": {"type": "string", "enum": ["asc", "desc"]},
                        },
                        "required": ["field", "direction"],
                    },
                },
                "limit": {"type": "integer"},
            },
            "required": ["left", "right", "join_on"],
            "additionalProperties": False,
        },
    },
}

_JOIN_INTENT_RE = re.compile(
    r"(?:\b(?:va|và|kem|kèm|cung|cùng|so\s*sanh|so\s*sánh|so\s*voi|so\s*với|dua\s*theo|dựa\s*theo|tuong\s*ung|tương\s*ứng)\b|[;,])",
    re.I,
)

BASE_SPECS = [
    spec("search_semantic_datasets", "Danh sách tập dữ liệu tổng hợp đã duyệt và được cấp quyền (truyền tùy chọn query để lọc và lấy đủ trường của dataset phù hợp)", [], optional=["query"]),
    spec(
        "query_semantic_plan",
        "Chạy kế hoạch tổng hợp JSON theo tập dữ liệu được duyệt. Tham số plan_json là chuỗi JSON gồm: "
        "dataset (string), dimensions (mảng string), metrics (mảng string), "
        "filters (MẢNG object {\"field\":\"...\",\"op\":\"gte\"|\"lte\"|\"eq\"|\"contains\",\"value\":\"...\"}, KHÔNG dùng dict), "
        "order_by (mảng {\"field\":\"...\",\"direction\":\"asc\"|\"desc\"}), limit (số nguyên).",
        ["plan_json"],
    ),
    STRUCTURED_SEMANTIC_JOIN_SPEC,
    spec("search_knowledge", "Tìm tri thức nghiệp vụ có nguồn và trạng thái hiệu lực", ["query"]),
    spec("search_schema", "Tìm báo cáo và bảng cho phép theo câu hỏi", ["query"]),
    spec("describe_table", "Mô tả schema của một báo cáo cho phép", ["report_id"]),
]

_DEFAULT_STATUS_MESSAGES = {
    "search_semantic_datasets": "Đang tìm tập dữ liệu phân tích ERP/MES...",
    "query_semantic_plan": "Đang tổng hợp dữ liệu ERP/MES...",
    "query_semantic_join": "Đang đối chiếu và ghép dữ liệu ERP/MES...",
    "search_knowledge": "Đang tra cứu tài liệu nghiệp vụ...",
    "search_schema": "Đang tìm cấu trúc báo cáo phù hợp...",
    "describe_table": "Đang đọc mô tả báo cáo...",
}


def _spec_from_report(report: dict) -> dict | None:
    tool_name = report.get("tool_name")
    param_schema = report.get("param_schema")
    if not isinstance(tool_name, str) or not tool_name or not isinstance(param_schema, dict):
        return None
    required = [k for k, v in param_schema.items() if isinstance(v, dict) and v.get("required", True)]
    optional = [k for k, v in param_schema.items() if isinstance(v, dict) and not v.get("required", True)]
    description = report.get("tool_description") or report.get("title") or report.get("id") or tool_name
    return spec(tool_name, description, required, optional)


class ReportBackend:
    specs = list(BASE_SPECS)
    names = {s["function"]["name"] for s in BASE_SPECS}

    def __init__(self, root, config, grants, db):
        self.root = Path(root).resolve()
        self.config, self.grants, self.db = config, grants, db
        self.reports = {r["id"]: r for r in config.get("reports", [])}
        self._report_by_tool: dict[str, str] = {}
        report_specs = []
        for report in config.get("reports", []):
            tool_name = report.get("tool_name")
            if isinstance(tool_name, str) and tool_name:
                self._report_by_tool[tool_name] = report["id"]
            tool_spec = _spec_from_report(report)
            if tool_spec:
                report_specs.append(tool_spec)
        self.specs = list(BASE_SPECS) + report_specs
        self.names = {s["function"]["name"] for s in self.specs}

    @classmethod
    def from_root(cls, root, grants, db):
        """Construct ReportBackend loading unified config + Entity-Fact semantic model."""
        return cls(root, load_erp_config(root), grants, db)

    def grant(self, user):
        # user is injected by the server, not accepted in tool arguments.
        if not isinstance(user, dict):
            return {}
        value = self.grants.get(str(user.get("id", "")))
        if not value and user.get("email"):
            value = self.grants.get(str(user.get("email", "")).lower())
        if not value and "*" in self.grants:
            value = self.grants["*"]
        value = value or {}
        if not isinstance(value, dict) or type(value.get("erp_user_id")) is not int or value["erp_user_id"] <= 0:
            return {}
        return value

    def authorized(self, user):
        return bool(self.grant(user).get("reports") or self.grant(user).get("semantic_datasets"))

    def allowed(self, user):
        return {k: v for k, v in self.reports.items() if k in self.grant(user).get("reports", [])}

    def read(self, relative):
        path = (self.root / relative).resolve()
        if not path.is_relative_to(self.root) or path.stat().st_size > 200000:
            raise ValueError("invalid configured asset")
        return path.read_text()

    def status_message(self, name: str) -> str:
        report_id = self._report_by_tool.get(name)
        if report_id and report_id in self.reports:
            msg = self.reports[report_id].get("status_message")
            if isinstance(msg, str) and msg.strip():
                return msg
        return _DEFAULT_STATUS_MESSAGES.get(name, f"Đang tra cứu {name}...")

    def missing_args_hint(self, name: str) -> str:
        report_id = self._report_by_tool.get(name)
        if report_id and report_id in self.reports:
            custom_hint = self.reports[report_id].get("missing_args_hint")
            if isinstance(custom_hint, str) and custom_hint.strip():
                return custom_hint
        spec_def = next((s for s in self.specs if s["function"]["name"] == name), None)
        if spec_def:
            required = spec_def["function"]["parameters"].get("required") or []
            if required:
                return f"Tool {name} yêu cầu đủ các tham số hợp lệ: {', '.join(required)}."
        contracts = self.config.get("semantic_contracts") or {}
        ds_candidate = name.removeprefix("query_") if isinstance(name, str) else ""
        if ds_candidate in contracts or name in contracts:
            ds_id = ds_candidate if ds_candidate in contracts else name
            return (
                f"Tool '{name}' không tồn tại. '{ds_id}' là tên dataset semantic — "
                f"HÃY GỌI `query_semantic_plan` với `dataset='{ds_id}'`."
            )
        return ""

    def is_direct_render(self, name: str) -> bool:
        report_id = self._report_by_tool.get(name)
        return bool(report_id and report_id in self.reports and self.reports[report_id].get("direct_render"))

    def person_lookup_tool(self) -> str:
        for report in self.reports.values():
            if report.get("person_lookup") and isinstance(report.get("tool_name"), str):
                return report["tool_name"]
        return ""

    def schema(self, report):
        result = {k: report[k] for k in ("id", "title", "tables", "join", "fields", "validation")}
        # The manifest is metadata, not an authorization grant or executable SQL.
        # Include only fields already exposed by the independently granted report.
        try:
            manifest = json.loads(self.read(report["manifest"]))
            if not isinstance(manifest, dict):
                raise ValueError("invalid manifest")
            fields = set(report["fields"])
            columns = manifest.get("columns", [])
            inputs = manifest.get("inputs", {})
            output = manifest.get("output", {})
            filters = inputs.get("filters", []) if isinstance(inputs, dict) else []
            metrics = output.get("metrics", []) if isinstance(output, dict) else []
            if not all(isinstance(v, list) for v in (columns, filters, metrics, manifest.get("match_phrases", []))):
                raise ValueError("invalid semantic metadata")
            result["semantic_metadata"] = {
                "phrases": [v for v in manifest.get("match_phrases", []) if isinstance(v, str)][:30],
                "columns": [{k: col[k] for k in ("field", "label", "aliases") if k in col}
                            for col in columns if isinstance(col, dict) and col.get("field") in fields],
                "filters": [{k: f[k] for k in ("parameter", "column", "aliases", "value_type") if k in f}
                            for f in filters if isinstance(f, dict) and f.get("column") in fields],
                "metrics": [m for m in metrics if isinstance(m, str) and m in fields],
                "manifest_validation": manifest.get("validation", {}),
                "provenance": report["manifest"],
                "notice": "Metadata chưa xác minh không phải bằng chứng dữ liệu hoặc công thức đã duyệt.",
            }
        except (OSError, ValueError, TypeError, KeyError):
            # Missing or invalid metadata must not turn into an inferred definition.
            result["semantic_metadata"] = {"status": "unavailable"}
        return result

    def semantic_datasets_for(self, user, *, include_cues: bool = True):
        contracts = self.config.get("semantic_contracts", {})
        allowed = set(self.grant(user).get("semantic_datasets", []))
        datasets = []
        for key in sorted(allowed):
            contract = contracts.get(key, {})
            if not isinstance(contract, dict) or contract.get("status") != "approved" or contract.get("scope") not in ("erp_user_view", "sales_orders_scoped_v1", "curated_scoped_subquery"):
                continue
            unit_reqs = {
                m: md["unit_dimension"]
                for m, md in contract.get("metrics", {}).items()
                if isinstance(md, dict) and md.get("unit_dimension")
            }
            item = {
                "id": key,
                "version": contract.get("version"),
                "dimensions": sorted(contract.get("dimensions", {})),
                "metrics": sorted(contract.get("metrics", {})),
                "filters": sorted(contract.get("filters", {})),
                "require_bounded_date": contract.get("require_bounded_date", True),
            }
            if contract.get("title"):
                item["title"] = contract["title"]
            if contract.get("max_date_span_days") and int(contract["max_date_span_days"]) < 366:
                item["max_date_span_days"] = int(contract["max_date_span_days"])
            if contract.get("notes"):
                item["notes"] = contract["notes"]
            if unit_reqs:
                item["unit_requirements"] = unit_reqs
            if include_cues:
                if contract.get("cues"):
                    item["cues"] = contract["cues"]
                if contract.get("secondary_cues"):
                    item["secondary_cues"] = contract["secondary_cues"]
            datasets.append(item)
        return datasets

    def retrieve(self, query, user, history=()):
        terms, allowed = tokens(query), self.allowed(user)
        candidates = [self.schema(r) for r in allowed.values()]
        scored = [(len(terms & tokens(json.dumps(s, ensure_ascii=False))), s) for s in candidates]
        schemas = [s for score, s in sorted(scored, key=lambda x: -x[0]) if score][:3]
        matches = []
        for doc in self.config.get("knowledge", []):
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
        result = {"schemas": schemas, "sources": selected, "conflicts": conflicts}
        semantic_datasets = self.semantic_datasets_for(user, include_cues=False)
        scoring_datasets = self.semantic_datasets_for(user, include_cues=True)
        contracts = self.config.get("semantic_contracts", {})
        hints = extract_context_hints(
            query,
            history=history,
            datasets=scoring_datasets,
            person_cues=self.config.get("person_cues"),
            person_lookup_tool=self.person_lookup_tool(),
            contracts=contracts,
        )
        if hints:
            result["context_hints"] = hints
        if semantic_datasets:
            if len(semantic_datasets) <= 16:
                result["semantic_datasets"] = semantic_datasets
            else:
                rec_ids = [d["id"] for d in (hints or {}).get("recommended_datasets", []) if isinstance(d, dict) and d.get("id")]
                ds_by_id = {ds["id"]: ds for ds in semantic_datasets}
                if rec_ids:
                    result["semantic_datasets"] = [ds_by_id[i] for i in rec_ids if i in ds_by_id]
                result["other_datasets"] = [
                    f"{ds['id']}: {ds.get('title', ds['id'])}"
                    for ds in semantic_datasets
                    if ds["id"] not in rec_ids
                ]
        return result

    def _wants_cross_dataset_join(self, question: str, history=(), user=None) -> bool:
        if not question or not _JOIN_INTENT_RE.search(question):
            return False
        scoring = self.semantic_datasets_for(user, include_cues=True) if user is not None else []
        if len(scoring) < 2:
            return False
        hints = extract_context_hints(
            question,
            history=history,
            datasets=scoring,
            contracts=self.config.get("semantic_contracts", {}),
        )
        return bool(hints.get("available_joins"))

    def model_specs(self, question="", history=(), user=None):
        """Return a pruned, typed tool subset tailored to grants and config cues."""
        grant = self.grant(user) if user is not None else {}
        has_semantic = bool(grant.get("semantic_datasets"))
        has_reports = bool(grant.get("reports"))
        include_join = has_semantic and self._wants_cross_dataset_join(question, history=history, user=user)
        if has_semantic and not has_reports:
            base = [s for s in self.specs if s["function"]["name"] == "search_semantic_datasets"] + [STRUCTURED_SEMANTIC_SPEC]
            if include_join:
                base.append(STRUCTURED_SEMANTIC_JOIN_SPEC)
            return base

        core_names = {"search_semantic_datasets", "search_knowledge"}
        retired_when_semantic = {"search_schema", "describe_table"}
        user_msgs = [
            str(m.get("content") or "")
            for m in (history or ())[-4:]
            if isinstance(m, dict) and m.get("role") == "user" and isinstance(m.get("content"), str)
        ]
        history_text = " ".join(user_msgs)
        text = _norm_hint_text(f"{history_text} {question}")
        detected_keys = {
            k
            for msg in (*user_msgs, question or "")
            if msg
            for k, v in extract_entities(msg).items()
            if v
        }
        selected_lookups = set()

        for report in self.reports.values():
            tool_name = report.get("tool_name")
            if not tool_name:
                continue
            if report.get("core_tool"):
                core_names.add(tool_name)
            if report.get("retired_when_semantic"):
                retired_when_semantic.add(tool_name)
            req_entities = report.get("require_detected_entities") or ()
            if req_entities and not all(ent in detected_keys for ent in req_entities):
                continue
            cues = report.get("cues") or ()
            exclude_cues = report.get("exclude_cues") or ()
            matched_cue = any(
                has_word_cue(text, cue) if len(cue) <= 4 else (has_word_cue(text, cue) or (" " in cue and cue in text))
                for cue in cues
            )
            excluded = any(
                has_word_cue(text, cue) if len(cue) <= 4 else (has_word_cue(text, cue) or (" " in cue and cue in text))
                for cue in exclude_cues
            )
            if matched_cue and not excluded:
                selected_lookups.add(tool_name)

        out = []
        for s in self.specs:
            name = s["function"]["name"]
            if name == "query_semantic_plan":
                out.append(STRUCTURED_SEMANTIC_SPEC)
            elif name == "query_semantic_join":
                if include_join:
                    out.append(STRUCTURED_SEMANTIC_JOIN_SPEC)
            elif name in core_names:
                out.append(s)
            elif has_semantic and name in retired_when_semantic:
                continue
            elif name in selected_lookups:
                out.append(s)
        return out

    def validate(self, name, args):
        if name == "query_semantic_join":
            if not isinstance(args, dict):
                raise ValueError("arguments")
            allowed_keys = {"left", "right", "extra_legs", "join_on", "join_type", "order_by", "limit"}
            if not {"left", "right", "join_on"}.issubset(set(args)) or not set(args).issubset(allowed_keys):
                raise ValueError("arguments")
            if not isinstance(args.get("left"), dict) or not isinstance(args.get("right"), dict):
                raise ValueError("arguments")
            if "extra_legs" in args and args["extra_legs"] is not None:
                extra = args["extra_legs"]
                if not isinstance(extra, list) or len(extra) > 1 or any(not isinstance(x, dict) for x in extra):
                    raise ValueError("arguments")
            if not isinstance(args.get("join_on"), str) or not args["join_on"].strip():
                raise ValueError("arguments")
            return
        if name == "query_semantic_plan":
            if not isinstance(args, dict):
                raise ValueError("arguments")
            if "plan_json" in args:
                if len(args) != 1 or not isinstance(args["plan_json"], (str, dict)):
                    raise ValueError("arguments")
                if isinstance(args["plan_json"], str) and (not args["plan_json"].strip() or len(args["plan_json"]) > 2000):
                    raise ValueError("arguments")
                return
            allowed_keys = {"dataset", "dimensions", "metrics", "filters", "order_by", "limit"}
            if "dataset" not in args or not set(args).issubset(allowed_keys):
                raise ValueError("arguments")
            if not isinstance(args.get("dataset"), str) or not args["dataset"].strip():
                raise ValueError("arguments")
            return
        param_def = next(s["function"]["parameters"] for s in self.specs if s["function"]["name"] == name)
        fields, all_props = param_def["required"], set(param_def["properties"])
        if not isinstance(args, dict) or not set(fields).issubset(set(args)) or not set(args).issubset(all_props):
            raise ValueError("arguments")

        report_id = self._report_by_tool.get(name)
        report = self.reports.get(report_id, {}) if report_id else {}
        param_schema = report.get("param_schema") or {}
        for key, value in args.items():
            max_len = int((param_schema.get(key) or {}).get("max_len", 500))
            if not isinstance(value, str) or not value.strip() or len(value) > max_len:
                raise ValueError("arguments")

        for key, rule in param_schema.items():
            if key not in args or not isinstance(rule, dict):
                continue
            val = args[key]
            kind = rule.get("type")
            if kind == "date":
                date.fromisoformat(val)
            elif kind == "identifier":
                if not re.fullmatch(r"[\w./-]{1,64}", val):
                    raise ValueError("filters")
        if "date_from" in args and "date_to" in args:
            start, end = date.fromisoformat(args["date_from"]), date.fromisoformat(args["date_to"])
            max_span = int(report.get("max_date_span_days", 62))
            if not 0 <= (end - start).days <= max_span:
                raise ValueError("filters")

    async def _probe_distinct_filter_values(self, contract: dict, plan: dict, erp_user_id: int, limits) -> str:
        """Probe actual distinct values in DB under RLS when a text filter returns 0 rows."""
        if not isinstance(contract, dict) or contract.get("scope") != "curated_scoped_subquery":
            return ""
        source_sql = contract.get("source_sql")
        user_param_count = contract.get("user_param_count", 1)
        if not isinstance(source_sql, str) or not source_sql.strip() or type(user_param_count) is not int or user_param_count < 0:
            return ""
        fdefs = contract.get("filters") or {}
        plan_filters = plan.get("filters") or []
        if not isinstance(plan_filters, list):
            return ""

        text_target = None
        date_where: list[str] = []
        date_params: list = []
        op_map = {"eq": "=", "gte": ">=", "lte": "<="}
        for item in plan_filters:
            if not isinstance(item, dict):
                continue
            fname, op, val = item.get("field"), item.get("op"), item.get("value")
            fdef = fdefs.get(fname)
            if not isinstance(fdef, dict):
                continue
            if fdef.get("type") == "date" and op in op_map and isinstance(val, str):
                date_where.append(f"{identifier(fdef['column'])} {op_map[op]} %s")
                date_params.append(val)
            elif fdef.get("type") == "text" and text_target is None and isinstance(val, str) and val.strip():
                text_target = (fname, fdef["column"], val.strip())

        if text_target is None:
            return ""
        if contract.get("require_bounded_date", True) and not date_where:
            return ""

        fname, col_name, fval = text_target
        col_ident = identifier(col_name)
        norm_val = normalize_text(fval)
        where_parts = [*date_where, f"nullif(trim(coalesce({col_ident}::text, '')), '') IS NOT NULL"]
        params: list = [erp_user_id] * user_param_count + date_params
        if norm_val:
            order_expr = (
                f"(CASE WHEN strpos(lower(translate(coalesce({col_ident}::text, ''), '{_VN_SRC}', '{_VN_DST}')), %s) > 0 "
                f"THEN 0 ELSE 1 END), 1"
            )
            params.append(norm_val)
        else:
            order_expr = "1"
        probe_sql = (
            f"SELECT {col_ident} AS val FROM ({source_sql}) AS _probe "
            f"WHERE {' AND '.join(where_parts)} GROUP BY {col_ident} ORDER BY {order_expr} LIMIT 12"
        )
        try:
            rows = await self.db(probe_sql, tuple(params), limits)
        except Exception:
            return ""
        if not isinstance(rows, list):
            return ""
        vals: list[str] = []
        seen = set()
        for r in rows:
            if not isinstance(r, dict) or r.get("val") in (None, ""):
                continue
            v = str(r["val"]).strip()
            if v and v not in seen:
                seen.add(v)
                vals.append(v)
        if not vals:
            return ""
        return (
            f"Không có dữ liệu khớp '{fname}={fval}'. Giá trị thực tế hiện có cho '{fname}' trong phạm vi này: "
            f"{', '.join(vals[:12])}. Hãy gọi lại query_semantic_plan với giá trị khớp chính xác hoặc bỏ bộ lọc '{fname}' nếu muốn xem toàn bộ."
        )

    def _suggest_datasets_for_error(
        self,
        user,
        *,
        ds_id: str | None = None,
        parsed_plan: dict | None = None,
    ) -> tuple[list[dict], str]:
        scoring = self.semantic_datasets_for(user, include_cues=True)
        contracts = self.config.get("semantic_contracts", {})
        parts = [str(ds_id or "").replace("_", " ")]
        if isinstance(parsed_plan, dict):
            for k in ("dimensions", "metrics"):
                vals = parsed_plan.get(k)
                if isinstance(vals, list):
                    parts.extend(str(v).replace("_", " ") for v in vals)
            for f in parsed_plan.get("filters") or ():
                if isinstance(f, dict) and f.get("field"):
                    parts.append(str(f["field"]).replace("_", " "))
        query_text = " ".join(p for p in parts if p).strip() or "tong hop erp mes"
        ranked = rank_datasets(
            query_text,
            datasets=scoring,
            contracts=contracts,
            field_catalog=self.config.get("field_catalog"),
        )
        suggestions = []
        for score, ds in ranked[:6]:
            if score <= 0 and suggestions:
                break
            suggestions.append({
                "id": ds["id"],
                "title": ds.get("title", ds["id"]),
                "dimensions": ds.get("dimensions", ())[:12],
                "metrics": ds.get("metrics", ()),
                "filters": ds.get("filters", ())[:12],
                "require_bounded_date": ds.get("require_bounded_date", True),
            })
        if not suggestions and scoring:
            suggestions = [
                {
                    "id": ds["id"],
                    "title": ds.get("title", ds["id"]),
                    "dimensions": ds.get("dimensions", ())[:12],
                    "metrics": ds.get("metrics", ()),
                    "filters": ds.get("filters", ())[:12],
                    "require_bounded_date": ds.get("require_bounded_date", True),
                }
                for ds in scoring[:6]
            ]
        allowed_reports = self.allowed(user)
        clean_id = (ds_id or "").strip().removeprefix("query_")
        matched_report = allowed_reports.get(clean_id)
        if not matched_report:
            matched_report = next(
                (r for r in allowed_reports.values() if r.get("tool_name") in (ds_id, f"query_{clean_id}")),
                None,
            )
        extra_note = ""
        if matched_report and not matched_report.get("retired_when_semantic") and not matched_report.get("require_detected_entities"):
            extra_note = f" ('{ds_id}' là tên báo cáo `{matched_report.get('tool_name')}`, không phải dataset semantic)"
        elif matched_report:
            extra_note = f" ('{ds_id}' là báo cáo tra cứu đơn lẻ theo mã cụ thể, KHÔNG phải dataset tổng hợp semantic)"
        hint = (
            f"Dataset '{ds_id}' không hợp lệ hoặc không được phép{extra_note}. "
            "KHÔNG tự bịa tên dataset; hãy chọn ĐÚNG một `id` trong `suggested_datasets` "
            "(hoặc gọi `search_semantic_datasets`) và GỌI LẠI NGAY `query_semantic_plan`."
        )
        return suggestions, hint

    async def execute(self, name, args, user, limits):
        if not self.authorized(user):
            return {"error": "forbidden"}
        self.validate(name, args)
        if name == "search_semantic_datasets":
            query_text = str(args.get("query") or "").strip() if isinstance(args, dict) else ""
            full_list = self.semantic_datasets_for(user, include_cues=False)
            contracts = self.config.get("semantic_contracts", {})
            if query_text:
                scored = score_datasets(query_text, (), self.semantic_datasets_for(user, include_cues=True), contracts=contracts)
                matched = [
                    {k: v for k, v in ds.items() if k not in ("cues", "secondary_cues")}
                    for score, ds in scored
                    if score > 0
                ][:8]
                return {"datasets": matched or [ds for _, ds in scored[:8]], "sources": []}
            if len(full_list) <= 16:
                return {"datasets": full_list, "sources": []}
            return {
                "datasets": [
                    {
                        "id": ds["id"],
                        "title": ds.get("title", ds["id"]),
                        "require_bounded_date": ds.get("require_bounded_date", True),
                    }
                    for ds in full_list
                ],
                "hint": "Hãy gọi lại search_semantic_datasets với tham số query mô tả nghiệp vụ (hoặc mã dataset) để xem đủ dimensions/metrics/filters.",
                "sources": [],
            }
        if name == "query_semantic_plan":
            try:
                raw_plan = parse_plan_arguments(args)
                contracts = self.config.get("semantic_contracts", {})
                plan = normalize_semantic_plan(raw_plan, contracts, max_rows=limits.rows)
                res = await execute_plan(
                    plan,
                    contracts=contracts,
                    allowed_contracts=set(self.grant(user).get("semantic_datasets", [])),
                    erp_user_id=self.grant(user)["erp_user_id"],
                    db=self.db,
                    limits=limits,
                )
                if res.get("status") == "empty":
                    contract_meta = contracts.get(res.get("contract_id") or "", {})
                    fdefs = contract_meta.get("filters", {}) if isinstance(contract_meta, dict) else {}
                    alt_date = contract_meta.get("alternate_date_field") if isinstance(contract_meta, dict) else None
                    alt_label = contract_meta.get("alternate_date_label") or alt_date
                    plan_filters = plan.get("filters") or []
                    used_fields = {f.get("field") for f in plan_filters if isinstance(f, dict)}
                    contract_cues = {
                        str(c).strip().lower()
                        for key in ("cues", "secondary_cues")
                        for c in (contract_meta.get(key) or ())
                        if isinstance(c, str) and c.strip()
                    }
                    for f in plan_filters:
                        if not isinstance(f, dict) or f.get("op") != "eq":
                            continue
                        f_name = f.get("field")
                        f_val = str(f.get("value") or "").strip()
                        if isinstance(fdefs.get(f_name), dict) and fdefs[f_name].get("parent_prefix_fallback") and "-" in f_val:
                            base_prefix = f_val.rsplit("-", 1)[0]
                            if len(base_prefix) >= 5:
                                res["hint"] = (
                                    f"Không có dữ liệu khớp chính xác '{f_val}'; hãy thử gọi lại query_semantic_plan "
                                    f"với trường '{f_name}' op='contains' và value='{base_prefix}' (và ghi chú rõ nếu tìm thấy theo mã gốc)."
                                )
                                break
                    if "hint" not in res and contract_cues:
                        for f in plan_filters:
                            if not isinstance(f, dict):
                                continue
                            f_name = str(f.get("field") or "")
                            f_val = str(f.get("value") or "").strip()
                            f_def = fdefs.get(f_name) if isinstance(fdefs.get(f_name), dict) else {}
                            if f_def.get("type") == "text" and f_val.lower() in contract_cues:
                                res["hint"] = (
                                    f"Không có dữ liệu khớp '{f_name}={f_val}' vì '{f_val}' là tên loại chứng từ của dataset này chứ không phải giá trị cột '{f_name}'; "
                                    f"HÃY GỌI LẠI NGAY query_semantic_plan và BỎ bộ lọc '{f_name}'."
                                )
                                break
                    if "hint" not in res and alt_date and alt_date not in used_fields and contract_meta.get("date_field", "day") in used_fields:
                        res["hint"] = (
                            f"Không có dòng theo trường ngày mặc định ({contract_meta.get('date_field', 'day')}); "
                            f"HÃY GỌI TIẾP query_semantic_plan lọc theo '{alt_date}' ({alt_label}) với cùng điều kiện đối tượng và mốc ngày."
                        )
                    alt_filters = contract_meta.get("alternate_filter_fields") if isinstance(contract_meta, dict) else None
                    if "hint" not in res and isinstance(alt_filters, dict):
                        for f in plan_filters:
                            if not isinstance(f, dict) or f.get("op") not in ("eq", "contains"):
                                continue
                            f_name = f.get("field")
                            alt_field = alt_filters.get(f_name)
                            if isinstance(alt_field, str) and alt_field in fdefs and alt_field not in used_fields:
                                res["hint"] = (
                                    f"Không có dòng khớp '{f_name}={f.get('value')}'; hãy gọi tiếp query_semantic_plan "
                                    f"thay bộ lọc '{f_name}' bằng '{alt_field}' với giá trị '{f.get('value')}' (giữ nguyên khoảng ngày)."
                                )
                                break
                    if "hint" not in res:
                        for f in plan_filters:
                            if not isinstance(f, dict) or f.get("op") != "eq":
                                continue
                            f_name = str(f.get("field") or "")
                            f_val = str(f.get("value") or "").strip()
                            name_candidate = f"{f_name}_name" if f_name != "employee_code" else "employee_name"
                            looks_like_name = any(ch.isalpha() for ch in f_val) and (
                                " " in f_val or not any(ch.isdigit() for ch in f_val)
                            )
                            if f_val and looks_like_name and name_candidate in fdefs and name_candidate not in used_fields:
                                res["hint"] = (
                                    f"Không có dòng khớp mã chính xác '{f_name}={f_val}'; nếu '{f_val}' là tên gọi, "
                                    f"HÃY GỌI TIẾP query_semantic_plan thay bộ lọc '{f_name}' bằng '{name_candidate}' với op='contains' và value='{f_val}'."
                                )
                                break
                    if "hint" not in res:
                        probe_hint = await self._probe_distinct_filter_values(
                            contract_meta, plan, self.grant(user)["erp_user_id"], limits
                        )
                        if probe_hint:
                            res["hint"] = probe_hint
                return res
            except PlanError as exc:
                hints = {
                    "unit_dimension_required": "Metric yêu cầu đơn vị ('unit' cho quantity/in_qty/out_qty hoặc 'currency' cho nguyên tệ). ĐỪNG trả lời người dùng — HÃY GỌI LẠI NGAY query_semantic_plan sau khi thêm 'unit' vào dimensions (và thêm 'order_by' nếu chưa có).",
                    "order_required": "Khi có dimensions, bắt buộc truyền order_by (ví dụ [{\"field\":\"<metric>\",\"direction\":\"desc\"}]). HÃY GỌI LẠI NGAY query_semantic_plan với order_by đầy đủ.",
                    "bounded_date_range_required": "Bắt buộc lọc trường ngày (day) bằng 'eq' hoặc cặp 'gte' và 'lte' trong tối đa 366 ngày. HÃY GỌI LẠI NGAY query_semantic_plan.",
                    "ranking_requires_single_unit": "Xếp hạng theo tiền nguyên tệ yêu cầu lọc một loại currency (hoặc dùng metric *_vnd). HÃY GỌI LẠI NGAY query_semantic_plan.",
                    "invalid_fields": "Không đặt tên metric vào dimensions hoặc lặp trường giữa dimensions và metrics. HÃY SỬA VÀ GỌI LẠI NGAY query_semantic_plan.",
                    "dimension_forbidden": "Có trường không hợp lệ trong dimensions (chỉ dùng đúng tên trong valid_dimensions). HÃY SỬA VÀ GỌI LẠI NGAY query_semantic_plan.",
                    "metric_forbidden": "Có chỉ tiêu không hợp lệ trong metrics (chỉ dùng đúng tên trong valid_metrics). HÃY SỬA VÀ GỌI LẠI NGAY query_semantic_plan.",
                    "filter_forbidden": "Trường lọc hoặc toán tử lọc không được hỗ trợ (chỉ dùng đúng tên trong valid_filters). HÃY SỬA VÀ GỌI LẠI NGAY query_semantic_plan.",
                    "invalid_plan": "Cấu trúc plan chưa hợp lệ (tối đa 10 dimensions, 1-10 metrics). Kiểm tra valid_dimensions/valid_metrics/valid_filters và GỌI LẠI NGAY query_semantic_plan.",
                }
                err: dict[str, Any] = {"error": "invalid_semantic_plan", "error_code": str(exc)}
                if str(exc) in hints:
                    err["hint"] = hints[str(exc)]
                try:
                    parsed_plan = parse_plan_arguments(args)
                    ds_id = parsed_plan.get("dataset")
                except (PlanError, ValueError, TypeError):
                    parsed_plan = {}
                    ds_id = None
                c_meta = (self.config.get("semantic_contracts") or {}).get(ds_id or "")
                if isinstance(c_meta, dict) and c_meta.get("status") == "approved":
                    valid_dims = sorted(c_meta.get("dimensions") or {})
                    valid_metrics = sorted(c_meta.get("metrics") or {})
                    valid_filters = sorted(c_meta.get("filters") or {})
                    err["valid_dimensions"] = valid_dims
                    err["valid_metrics"] = valid_metrics
                    err["valid_filters"] = valid_filters
                    if str(exc) == "filter_forbidden" and isinstance(parsed_plan, dict):
                        f_meta = c_meta.get("filters") or {}
                        bad_fields = []
                        bad_ops = []
                        for f in parsed_plan.get("filters") or ():
                            if not isinstance(f, dict):
                                continue
                            fname, fop = f.get("field"), f.get("op")
                            if fname not in f_meta:
                                bad_fields.append(str(fname))
                            else:
                                fdef = f_meta.get(fname) or {}
                                allowed_ops = list(fdef.get("ops") or [])
                                if fdef.get("type") == "text" and "eq" in allowed_ops and "in" not in allowed_ops:
                                    allowed_ops.append("in")
                                if fop not in allowed_ops:
                                    bad_ops.append(f"{fname} (op={fop!r}, hỗ trợ {allowed_ops})")
                        if bad_ops and not bad_fields:
                            err["hint"] = f"Toán tử lọc không hợp lệ cho: {', '.join(bad_ops)}. Hãy sửa op và GỌI LẠI NGAY query_semantic_plan."
                        elif bad_fields or bad_ops:
                            bad_all = bad_fields + bad_ops
                            err["hint"] = f"Trường lọc hoặc toán tử không hợp lệ: {', '.join(bad_all)}. CHỈ dùng tên có trong valid_filters ({', '.join(valid_filters)}); hãy BỎ hoặc SỬA trường sai và GỌI LẠI NGAY query_semantic_plan."
                    elif str(exc) == "dimension_forbidden" and isinstance(parsed_plan, dict):
                        d_meta = c_meta.get("dimensions") or {}
                        bad = [str(d) for d in (parsed_plan.get("dimensions") or ()) if d not in d_meta]
                        if bad:
                            err["hint"] = f"Chiều phân tích không hợp lệ: {', '.join(bad)}. CHỈ dùng tên có trong valid_dimensions ({', '.join(valid_dims)}); hãy SỬA và GỌI LẠI NGAY query_semantic_plan."
                    elif str(exc) == "metric_forbidden" and isinstance(parsed_plan, dict):
                        m_meta = c_meta.get("metrics") or {}
                        bad = [str(m) for m in (parsed_plan.get("metrics") or ()) if m not in m_meta]
                        if bad:
                            err["hint"] = f"Chỉ tiêu không hợp lệ: {', '.join(bad)}. CHỈ dùng tên có trong valid_metrics ({', '.join(valid_metrics)}); hãy SỬA và GỌI LẠI NGAY query_semantic_plan."
                    elif str(exc) == "bounded_date_range_required":
                        d_fields = c_meta.get("bounded_date_fields") or [c_meta.get("date_field", "day")]
                        max_span = int(c_meta.get("max_date_span_days", 366))
                        err["hint"] = (
                            f"Bắt buộc lọc trường ngày ({', '.join(d_fields)}) bằng 'eq' hoặc cặp 'gte' và 'lte' "
                            f"trong tối đa {max_span} ngày. HÃY GỌI LẠI NGAY query_semantic_plan."
                        )
                    if c_meta.get("notes"):
                        err["notes"] = c_meta["notes"]
                elif str(exc) == "dataset_forbidden" or not isinstance(c_meta, dict):
                    suggestions, disambig_hint = self._suggest_datasets_for_error(
                        user, ds_id=ds_id, parsed_plan=parsed_plan
                    )
                    err["hint"] = disambig_hint
                    if suggestions:
                        err["suggested_datasets"] = suggestions
                return err
            except (ValueError, TypeError):
                return {"error": "invalid_semantic_plan", "error_code": "invalid_json"}
        if name == "query_semantic_join":
            try:
                contracts = self.config.get("semantic_contracts", {})
                join_plan = normalize_joined_plan(args, contracts, max_rows=limits.rows)
                return await execute_joined_plan(
                    join_plan,
                    contracts=contracts,
                    allowed_contracts=set(self.grant(user).get("semantic_datasets", [])),
                    erp_user_id=self.grant(user)["erp_user_id"],
                    db=self.db,
                    limits=limits,
                )
            except PlanError as exc:
                err_join: dict[str, Any] = {
                    "error": "invalid_semantic_plan",
                    "error_code": str(exc),
                    "hint": f"Lỗi kế hoạch ghép nối ({exc}). Kiểm tra left/right/extra_legs dataset, join_on nằm trong dimensions mọi vế và khoảng ngày bắt buộc; hoặc gọi tuần tự query_semantic_plan.",
                }
                if str(exc) == "dataset_forbidden" and isinstance(args, dict):
                    contracts = self.config.get("semantic_contracts", {})
                    for leg_candidate in (args.get("left"), args.get("right"), *(args.get("extra_legs") or ())):
                        if isinstance(leg_candidate, dict):
                            leg_ds = leg_candidate.get("dataset")
                            if not isinstance(contracts.get(leg_ds or ""), dict):
                                suggestions, disambig_hint = self._suggest_datasets_for_error(
                                    user, ds_id=leg_ds, parsed_plan=leg_candidate
                                )
                                err_join["hint"] = disambig_hint
                                if suggestions:
                                    err_join["suggested_datasets"] = suggestions
                                break
                return err_join
            except (ValueError, TypeError):
                return {"error": "invalid_semantic_plan", "error_code": "invalid_json"}
        if name in ("search_knowledge", "search_schema"):
            result = self.retrieve(args["query"], user)
            if name == "search_schema":
                result["sources"] = [self.report_source(self.reports[s["id"]]) for s in result["schemas"]]
            return result

        report_id = args.get("report_id") or self._report_by_tool.get(name)
        report = self.allowed(user).get(report_id)
        if not report:
            return {"error": "forbidden_report"}
        source = self.report_source(report)
        if name == "describe_table":
            return {"schema": self.schema(report), "sources": [source]}
        # SQL/identifiers never come from the model. Each report declares its binding order.
        bindings = dict(args, user_id=self.grant(user)["erp_user_id"], row_limit=limits.rows + 1)
        sql = self.read(report["query_file"])
        rows = await self.db(sql, tuple(bindings.get(k, "") if k not in ("user_id", "row_limit") else bindings[k] for k in report["parameters"]), limits)
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
            if report.get("summary_zero_on_empty", True):
                summary["total_quantity"] = 0.0

        # Only reviewed fields leave the adapter. No URL generation in this slice.
        rows = [{k: v for k, v in row.items() if k in report["fields"]} for row in rows]
        if report.get("validator") == "inventory_balance" and rows:
            error = (
                "INVENTORY_RESULT_TRUNCATED" if has_more
                else validate_inventory_balance_result(args["material"], rows)
            )
            if error:
                return {"error": "invalid_result", "error_code": error}
        max_ret = report.get("max_returned_rows")
        if isinstance(max_ret, int) and len(rows) > max_ret:
            rows = rows[:max_ret]
            has_more = True
        source_key = [report_id, self.grant(user)["erp_user_id"], args]
        source = dict(source, id="records:" + hashlib.sha256(json.dumps(source_key, sort_keys=True).encode()).hexdigest()[:16])
        result = {
            "rows": rows,
            "returned_rows": len(rows),
            "has_more": has_more,
            "sources": [source],
            "validation": report["validation"],
            "summary": summary,
        }
        if report.get("next_step_note"):
            result["next_step_note"] = report["next_step_note"]
        while rows and len(json.dumps(result, default=str, ensure_ascii=False)) > limits.result_chars:
            rows.pop()
            result.update(returned_rows=len(rows), has_more=True)
        return result

    @staticmethod
    def report_source(report):
        return {
            "id": "schema:" + report["id"],
            "path": report["manifest"],
            "title": report["title"],
            "tables": report["tables"],
            "validation": report["validation"],
        }
