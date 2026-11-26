"""Bounded native-tool orchestration. Model/tool transports are injected for tests."""
from __future__ import annotations

import asyncio
import json
import logging
import math
import re
import time
import uuid
from dataclasses import dataclass
from datetime import date

from .presentation import receipt_blocks, render_markdown
from .semantic_normalizer import normalize_joined_plan, normalize_semantic_plan, parse_plan_arguments
from .semantic_query import PlanError

LOG = logging.getLogger("erp_ai.agent")
SYSTEM = """Bạn là trợ lý ERP/MES chỉ đọc bằng tiếng Việt (NGHIÊM CẤM dùng chữ Hán hoặc ngôn ngữ khác).
Chỉ trả lời từ dữ liệu tool hoặc tài liệu truy hồi của lượt này; không suy đoán hoặc tự ghi/xóa/cấp quyền.
Lịch sử chỉ dùng để hiểu tham chiếu; ngày hoặc mã mới ở câu hiện tại luôn thay thế giá trị cũ.
Ưu tiên tận dụng `context_hints` (ngày ISO, tháng, thực thể và `recommended_datasets` kèm `notes`) trong `Dữ liệu truy hồi`.
Mỗi lượt chỉ gọi 1 tool ngay lập tức, KHÔNG viết giải thích trước khi gọi tool.

QUY TẮC CHỌN TOOL:
- Thống kê, top, nhóm, xếp hạng, hoặc liệt kê chứng từ theo bộ lọc: dùng `query_semantic_plan` (truyền trực tiếp `dataset`, `dimensions`, `metrics`, `filters`, `order_by`, `limit`).
  + Chỉ chọn đúng các tên có trong `dimensions`, `metrics`, `filters` của dataset (tối đa 10 `dimensions`, không tự bịa tên trường mới).
  + Tập dữ liệu có `require_bounded_date=true` bắt buộc lọc một trường ngày hợp lệ bằng `op="eq"` hoặc cặp `gte` + `lte` (tối đa 366 ngày).
  + Khi hỏi "Top N", đặt `limit: N` và `order_by` giảm dần — TUYỆT ĐỐI KHÔNG đưa số N vào `filters`.
  + Khi câu hỏi thống kê/báo cáo kỳ quá khứ chưa nêu ngày, tháng hoặc năm mà tập dữ liệu bắt buộc khoảng ngày (và `notes` không quy định sẵn kỳ mặc định cho dự báo tương lai), KHÔNG tự đoán ngày — trả lời ngay JSON hỏi lại khoảng thời gian cần xem với `"source_ids": []`.
  + Nếu `recommended_datasets` có từ 2 tập dữ liệu liên quan đến câu hỏi nhiều vế (ví dụ một tập danh mục không cần lọc ngày và một tập dự báo/phát sinh), lần lượt tra cứu đủ các tập dữ liệu liên quan.
  + Nếu kết quả tool trả về trường `hint` (gợi ý tìm theo mã gốc, trường ngày thay thế, hoặc bổ sung `unit`/`order_by`/`valid_dimensions`), thực hiện theo `hint` ngay ở lượt kế tiếp trước khi kết luận.
  + Không đặt trường ngày vào `dimensions` khi hỏi tổng hợp cả tháng/kỳ; chỉ đặt khi hỏi theo từng ngày.
- Khi câu hỏi đòi hỏi đối chiếu/kết hợp chỉ tiêu từ 2 tập dữ liệu có sẵn trong `available_joins` (ví dụ vừa xem dừng máy vừa xem OEE từng máy), có thể dùng `query_semantic_join` (hoặc gọi lần lượt `query_semantic_plan`).
- Khi đối tượng là nhân viên công ty hoặc người lập/đề nghị chứng từ (tên người, mã NV, username ERP): nếu chưa có mã NV hoặc `context_hints` có `suggested_lookup_tool`, gọi tool tra cứu danh mục nhân viên đó trước để lấy mã NV/`user_name`, rồi BẮT BUỘC gọi tiếp `query_semantic_plan` vào tập dữ liệu nghiệp vụ phù hợp (chú ý ghi chú phân biệt cột mã nhân viên vs username trong `notes`, và luôn thử tiếp trường thay thế nếu `hint` gợi ý). Không dừng lại ở bước tra danh mục nhân viên.
- Tra cứu chi tiết chuyên biệt (tồn kho sổ sách/theo kho, bảng giá/MOQ, BOM, quy cách đóng gói, khách hàng, đơn bán/giao hàng, tem QC/khuôn): dùng tool chuyên biệt tương ứng có trong danh sách tool.
- Khi tool trả `summary` (`total_records`, `total_quantity`, `total_revenue`) và `has_more=true`, dùng số tổng từ `summary`, không tự cộng nhẩm từ `rows`. Giữ nguyên mã `status` gốc nếu chưa có tên trạng thái.
- TUYỆT ĐỐI KHÔNG tự làm phép tính chia, tỷ lệ hoặc ước lượng từ các dòng mẫu khi backend chưa có chỉ tiêu tính sẵn; chỉ nêu các số liệu đã xác minh từ kết quả và nói rõ phần ước lượng chưa có công thức tự động.

ĐỊNH DẠNG ĐẦU RA CUỐI CÙNG:
Xuất DUY NHẤT 1 đối tượng JSON (không Markdown/prose kèm theo):
{"answer":"tóm tắt ngắn gọn 1-2 câu tiếng Việt","source_ids":["ID nguồn từ trường sources"]}.
Khi chưa có dữ liệu hoặc thiếu bộ lọc, hỏi/nêu rõ ngay trong `"answer"` với `"source_ids": []`. Không tạo URL."""


@dataclass(frozen=True)
class Limits:
    rounds: int = 6
    tools: int = 10
    db_queries: int = 4
    seconds: float = 120
    rows: int = 50
    result_chars: int = 12000
    context_chars: int = 48000

    def __post_init__(self):
        for value in vars(self).values():
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError("invalid agent limit")
        for key in ("rounds", "tools", "db_queries", "rows", "result_chars", "context_chars"):
            if type(getattr(self, key)) is not int:
                raise ValueError("integer limit required")
        if self.rows > 200 or self.context_chars > 80000:
            raise ValueError("limit exceeds reviewed ceiling")


def encode(value):
    return json.dumps(value, ensure_ascii=False, default=str)


def parse_final(content):
    """Accept a unique trailing JSON envelope; discard all unstructured prose.

    Qwen's observed output sometimes puts prose before its final JSON. Never
    treat that prose as a verified answer, nor select between multiple objects.
    """
    if not isinstance(content, str) or len(content) > 16000:
        raise ValueError("invalid final")
    decoder, candidates = json.JSONDecoder(), []
    for index, char in enumerate(content):
        if char != "{":
            continue
        try:
            value, end = decoder.raw_decode(content[index:])
        except ValueError:
            continue
        if isinstance(value, dict) and set(value) == {"answer", "source_ids"}:
            candidates.append((value, content[index + end:].strip()))
    if len(candidates) != 1 or candidates[0][1] not in ("", "```"):
        raise ValueError("ambiguous final")
    return candidates[0][0]


_FALLBACK_DIRECT_RENDER_TOOLS = frozenset({
    "query_receipt_lines",
    "query_inventory_balance",
    "query_sales_orders",
    "query_inventory_by_warehouse",
})

_MULTI_PART_RE = re.compile(
    r"(?:\b(?:va|và|kem|kèm|cung|cùng|so\s*sanh|so\s*sánh|so\s*voi|so\s*với|dua\s*theo|dựa\s*theo|nguyen\s*nhan|nguyên\s*nhân)\b|[;,])",
    re.I,
)


def _is_multi_part_question(question: str, seed: dict) -> bool:
    hints = (seed or {}).get("context_hints") or {}
    recs = hints.get("recommended_datasets") or []
    joins = hints.get("available_joins") or []
    if len(recs) < 2 and not joins:
        return False
    return bool(_MULTI_PART_RE.search(question or "")) or len(hints.get("detected_entities") or {}) >= 2


async def _notify(callback, msg):
    if not callback:
        return
    try:
        res = callback(msg)
        if asyncio.iscoroutine(res):
            await res
    except Exception:
        pass


async def run_agent(question, *, user, model, backend, limits=None, history=(), on_status=None):
    """History must come from the authenticated chat, never model tool arguments.

    Cancellation propagates to the async model and database adapters. No detached
    thread may commit a late result. Verified results survive normal deadlines.
    """
    limits = limits or Limits()
    request_id = str(uuid.uuid4())
    started = time.monotonic()
    deadline = started + limits.seconds
    verified, sources, seen = [], {}, set()
    counts = {"rounds": 0, "tools": 0, "db_queries": 0, "tool_errors": 0}
    backend_config = getattr(backend, "config", None)

    def finish(status, answer="Chưa đủ dữ liệu để trả lời.", cited=()):
        blocks = receipt_blocks(question if isinstance(question, str) else "", verified, status, config=backend_config)
        block_ids = [source_id for block in blocks for source_id in block.get("source_ids", [])]
        cited = list(dict.fromkeys([*cited, *block_ids]))
        display = render_markdown(blocks) if blocks else answer
        if blocks:
            answer = next((block["text"] for block in blocks if block["type"] == "summary"), answer)
        source_list = [sources[s] for s in cited if s in sources]
        LOG.info("erp_agent %s", encode(dict(request_id=request_id, status=status,
                 elapsed_ms=round((time.monotonic() - started) * 1000), **counts)))
        return dict(request_id=request_id, status=status, answer=answer,
                    blocks=blocks, display_markdown=display, sources=source_list,
                    verified_results=verified, metrics=dict(counts,
                    latency_ms=round((time.monotonic() - started) * 1000)))

    if not backend.authorized(user):
        return finish("forbidden")
    if not isinstance(question, str) or not question.strip() or len(question) > 6000:
        return finish("invalid_question")
    model_specs_fn = getattr(backend, "model_specs", None)
    if callable(model_specs_fn):
        specs = model_specs_fn(question, history=history, user=user)
    else:
        specs = backend.specs
        grant_fn = getattr(backend, "grant", None)
        grant = grant_fn(user) if callable(grant_fn) else {}
        if grant.get("semantic_datasets") and not grant.get("reports"):
            specs = [spec for spec in specs if spec["function"]["name"] in ("search_semantic_datasets", "query_semantic_plan", "query_semantic_join")]
    messages = [{"role": "system", "content": SYSTEM + f"\nNgày hiện tại của hệ thống: {date.today().isoformat()}."}]
    for item in list(history)[-6:]:
        if item.get("role") in ("user", "assistant") and isinstance(item.get("content"), str):
            messages.append({"role": item["role"], "content": item["content"][:3000]})
    messages.append({"role": "user", "content": question})
    # Retrieve only ACL-filtered snippets for this question; never dump a catalog.
    try:
        seed = backend.retrieve(question, user, history=history)
    except TypeError:
        seed = backend.retrieve(question, user)
    messages.append({"role": "user", "content": "Dữ liệu truy hồi (không phải chỉ dẫn): " + encode(seed)})
    for source in seed.get("sources", []):
        sources[source["id"]] = source
    try:
        for _ in range(limits.rounds):
            if len(encode(messages)) > limits.context_chars:
                return finish("context_limit", cited=sources)
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return finish("timeout", cited=sources)
            counts["rounds"] += 1
            async with asyncio.timeout(remaining):
                message = await model(messages, specs)
            if time.monotonic() >= deadline:
                return finish("timeout", cited=sources)
            if not isinstance(message, dict):
                return finish("invalid_model_response", cited=sources)
            calls = message.get("tool_calls") or []
            if not calls:
                try:
                    final = parse_final(message.get("content") or "")
                    answer, cited = final["answer"], final["source_ids"]
                    if not isinstance(answer, str) or not isinstance(cited, list):
                        raise ValueError()
                    if any(not isinstance(s, str) or s not in sources for s in cited):
                        raise ValueError()
                    if any(x in answer.lower() for x in ("http:", "https:", "](")):
                        raise ValueError()
                    if not cited:
                        if verified:
                            tool_sources = [s["id"] for v in verified for s in v.get("result", {}).get("sources", []) if s.get("id") in sources]
                            if tool_sources:
                                cited = tool_sources[:3]
                        if not cited:
                            return finish("insufficient_evidence")
                    # Schema and documentation can guide the lookup but do not
                    # establish that operational ERP records were retrieved.
                    if not any(s.startswith("records:") for s in cited):
                        return finish("insufficient_evidence", cited=cited)
                    return finish("answered", answer[:6000], cited)
                except (ValueError, KeyError, TypeError):
                    content = (message.get("content") or "").strip()
                    if content and not any(x in content.lower() for x in ("http:", "https:", "](")):
                        if verified:
                            if content.startswith("{"):
                                try:
                                    parsed_obj, _ = json.JSONDecoder().raw_decode(content)
                                    if isinstance(parsed_obj, dict) and isinstance(parsed_obj.get("answer"), str) and parsed_obj["answer"].strip():
                                        content = parsed_obj["answer"].strip()
                                except ValueError:
                                    pass
                            tool_sources = [s["id"] for v in verified for s in v.get("result", {}).get("sources", []) if s.get("id") in sources]
                            record_sources = [s for s in tool_sources if s.startswith("records:")]
                            if record_sources:
                                return finish("answered", content[:6000], record_sources[:3])
                        elif not any(ch in content for ch in "{}") and (
                            "?" in content
                            or any(tok in content.lower() for tok in ("khoảng thời gian", "thời gian", "ngày nào", "tháng nào", "cần xem", "vui lòng cho biết", "bổ sung"))
                        ):
                            return finish("insufficient_evidence", content[:6000])
                    return finish("invalid_final", cited=sources)
            if not isinstance(calls, list) or len(calls) > limits.tools - counts["tools"]:
                return finish("tool_limit", cited=sources)
            ids = [c.get("id") for c in calls if isinstance(c, dict)]
            if len(ids) != len(calls) or any(not isinstance(i, str) or not i for i in ids) or len(set(ids)) != len(ids):
                return finish("invalid_tool_calls", cited=sources)
            messages.append({"role": "assistant", "content": None, "tool_calls": calls})
            # Sequential execution is intentional: a call can depend on prior evidence.
            for call in calls:
                counts["tools"] += 1
                tool_started = time.monotonic()
                name = "invalid"
                try:
                    fn = call["function"]
                    name = fn["name"]
                    if name not in backend.names:
                        raise ValueError("unknown_tool")
                    raw = fn["arguments"]
                    if not isinstance(raw, str) or len(raw) > 4000:
                        raise ValueError("invalid_arguments")
                    args = json.loads(raw)
                    backend.validate(name, args)
                    if name == "query_semantic_plan":
                        from .semantic_request import require_explicit_month
                        contracts = backend.config.get("semantic_contracts", {})
                        semantic_plan = normalize_semantic_plan(
                            parse_plan_arguments(args),
                            contracts,
                            max_rows=limits.rows,
                            question=question,
                        )
                        contract = contracts.get(semantic_plan.get("dataset"), {}) if isinstance(semantic_plan, dict) else {}
                        filter_defs = contract.get("filters", {}) if isinstance(contract, dict) else {}
                        date_fields = {
                            field for field, definition in filter_defs.items()
                            if isinstance(definition, dict) and definition.get("type") == "date"
                        }
                        require_explicit_month(question, semantic_plan, date_fields)
                        args = {"plan_json": json.dumps(semantic_plan, ensure_ascii=False)}
                    elif name == "query_semantic_join":
                        from .semantic_request import require_explicit_month
                        contracts = backend.config.get("semantic_contracts", {})
                        args = normalize_joined_plan(args, contracts, max_rows=limits.rows, question=question)
                        for leg_key in ("left", "right"):
                            leg = args.get(leg_key) or {}
                            c = contracts.get(leg.get("dataset"), {}) if isinstance(leg, dict) else {}
                            if isinstance(c, dict) and c.get("require_bounded_date", True):
                                f_defs = c.get("filters") or {}
                                d_fields = {f for f, fd in f_defs.items() if isinstance(fd, dict) and fd.get("type") == "date"}
                                require_explicit_month(question, leg, d_fields)
                    fingerprint = encode([name, sorted(args.items())])
                    if fingerprint in seen:
                        return finish("no_progress", cited=sources)
                    seen.add(fingerprint)
                    if name.startswith("query_"):
                        if counts["db_queries"] >= limits.db_queries:
                            return finish("db_limit", cited=sources)
                        counts["db_queries"] += 1
                    if on_status:
                        status_fn = getattr(backend, "status_message", None)
                        status_msg = status_fn(name) if callable(status_fn) else f"Đang tra cứu {name}..."
                        await _notify(on_status, status_msg)
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return finish("timeout", cited=sources)
                    async with asyncio.timeout(remaining):
                        result = await backend.execute(name, args, user, limits)
                    if time.monotonic() >= deadline:
                        return finish("timeout", cited=sources)
                    if len(encode(result)) > limits.result_chars:
                        raise ValueError("result_too_large")
                    if result.get("error"):
                        counts["tool_errors"] += 1
                        if result.get("error") == "invalid_semantic_plan" and result.get("error_code") not in ("invalid_result", "invalid_result_shape") and name.startswith("query_"):
                            counts["db_queries"] = max(0, counts["db_queries"] - 1)
                    else:
                        verified.append({"tool": name, "arguments": args, "result": result})
                        for source in result.get("sources", []):
                            sources[source["id"]] = source
                except PlanError as exc:
                    counts["tool_errors"] += 1
                    hint = (
                        "plan_json phải là chuỗi JSON hợp lệ dùng dấu nháy kép \", không dùng nháy đơn '; hãy kiểm tra và GỌI LẠI NGAY query_semantic_plan."
                        if str(exc) == "invalid_json" else
                        "Kiểm tra filters phải là MẢNG [{\"field\":\"day\",\"op\":\"gte\",\"value\":\"YYYY-MM-DD\"},{\"field\":\"day\",\"op\":\"lte\",\"value\":\"YYYY-MM-DD\"}] giữ đúng kỳ người dùng hỏi; ĐỪNG trả lời người dùng — hãy gọi lại ngay query_semantic_plan."
                    )
                    result = {
                        "error": "invalid_semantic_plan",
                        "error_code": str(exc),
                        "hint": hint,
                    }
                except (ValueError, KeyError, TypeError):
                    counts["tool_errors"] += 1
                    hint_fn = getattr(backend, "missing_args_hint", None)
                    hint = hint_fn(name) if callable(hint_fn) else ""
                    result = {"error": "invalid_tool_or_arguments"}
                    if hint:
                        result["hint"] = hint
                messages.append({"role": "tool", "tool_call_id": call["id"], "content": encode(result)})
                LOG.info("erp_tool %s", encode(dict(request_id=request_id,
                         tool=name if name in backend.names else "invalid", error=result.get("error"),
                         source_ids=[s["id"] for s in result.get("sources", [])],
                         elapsed_ms=round((time.monotonic() - tool_started) * 1000))))
            # Never let a language model present a partial or NULL aggregate as
            # a complete result. Preserve evidence, but state the actual limit.
            multi_part_question = _is_multi_part_question(question if isinstance(question, str) else "", seed)
            if (len(calls) == 1 and len(verified) == 1
                    and verified[0]["tool"] in ("query_semantic_plan", "query_semantic_join")):
                semantic_result = verified[0]["result"]
                status = semantic_result.get("status")
                contract_id = semantic_result.get("contract_id") or ""
                contract_notes = ((backend.config.get("semantic_contracts") or {}).get(contract_id) or {}).get("notes") or ""
                empty_msg = "Không tìm thấy dòng phù hợp với điều kiện và quyền truy cập hiện tại."
                if contract_notes:
                    empty_msg += f" Lưu ý dữ liệu hệ thống: {contract_notes}"
                messages_for_status = {
                    "partial": "Kết quả chưa đầy đủ vì vượt giới hạn hiển thị; chưa thể kết luận cho toàn bộ danh sách.",
                    "empty": empty_msg,
                    "missing": "Chỉ tiêu có giá trị trống; chưa đủ căn cứ kết luận là số 0 hoặc không có dữ liệu.",
                }
                if not semantic_result.get("hint") and status in messages_for_status and not multi_part_question:
                    return finish(status, messages_for_status[status],
                                  [s["id"] for s in semantic_result.get("sources", [])])
            # Reports marked direct_render have deterministic display blocks; another
            # model pass could change a confirmed value or turn missing data into zero.
            if len(calls) == 1 and len(verified) == 1 and counts["tool_errors"] == 0:
                direct_fn = getattr(backend, "is_direct_render", None)
                is_direct = (
                    direct_fn(verified[0]["tool"]) if callable(direct_fn)
                    else (verified[0]["tool"] in _FALLBACK_DIRECT_RENDER_TOOLS)
                )
                if is_direct:
                    return finish("answered", cited=[s["id"] for s in verified[0]["result"].get("sources", [])])
        return finish("round_limit", cited=sources)
    except (TimeoutError, asyncio.TimeoutError):
        return finish("timeout", cited=sources)
    except asyncio.CancelledError:
        finish("cancelled")
        raise
    except Exception as exc:
        if any(tok in exc.__class__.__name__.lower() for tok in ("timeout", "querycanceled")) or "statement timeout" in str(exc).lower():
            return finish("timeout", cited=sources)
        # Deliberately omit transport/DB exception text: it can contain secrets.
        return finish("backend_error", cited=sources)
