"""
title: HTMP ERP
author: HTMP Platform
version: 1.1.0
required_open_webui_version: 0.6.0
"""

"""Explicit ERP-only profile for the HTMP workspace model."""

import re
import unicodedata

from open_webui.utils.middleware import add_or_update_system_message
from open_webui.utils.misc import get_last_user_message


# Vietnamese phrasing varies widely in short ERP follow-ups.  These are
# semantic cues, normalized by the inlet before matching (no accents/case).
CONTINUATION_CUES = (
    "the con", "con ma", "thi sao", "ma khac", "hang khac",
    "vat tu khac", "san pham khac", "cai khac", "tiep theo", "tuong tu",
)
INTENT_TERMS = {
    "customer": ("khach hang", "khach", "nguoi mua", "doi tac"),
    "quantity": ("so luong", "sl", "bao nhieu", "so luong xuat", "so luong ban", "so luong giao"),
    "revenue": ("doanh thu", "doanh so", "tien ban", "gia tri ban"),
    "inventory": ("ton kho", "ton", "con hang"),
    "price": ("gia", "don gia", "bao gia"),
}


def request_intents(text: str) -> set[str]:
    """Return coarse ERP intents used only to decide context inheritance."""
    normalized = unicodedata.normalize("NFD", str(text).lower())
    normalized = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized.replace("đ", "d")).strip()
    return {
        intent for intent, terms in INTENT_TERMS.items()
        if any(re.search(rf"\b{re.escape(term)}\b", normalized) for term in terms)
    }


class Filter:
    async def inlet(
        self, body, __request__, __user__, __model__=None, __event_emitter__=None
    ):
        model_id = (__model__ or {}).get("id") or body.get("model")
        if model_id != "htmp-nhanh":
            return body
        # Regular Open WebUI chats do not inherit a model's toolIds. Attach the
        # read-only ERP tool before middleware resolves tools for this request.
        messages = body.get("messages", [])
        last_user_index = next((index for index in range(len(messages) - 1, -1, -1) if messages[index].get("role") == "user"), None)
        if last_user_index is not None:
            last_content = messages[last_user_index].get("content")
            normalized_last = re.sub(r"[^a-z0-9]+", " ", str(last_content).lower()).strip()
            # Do not cap the alphabetic prefix: valid ERP material codes such
            # as GCCKSC164 have six letters before their digits.  An explicit
            # code in the current turn must never be treated as a follow-up
            # referring to the previously remembered material.
            code_pattern = r"\b(?:\d{6,}|(?=[a-z0-9/-]*\d)(?=[a-z0-9/-]*[a-z])[a-z0-9]+(?:[-/][a-z0-9]+)*)\b"
            followup_words = (
                "đâu", "nào", "bao nhiêu", "thế", "còn", "thì sao",
                "khác", "tiếp theo", "tương tự",
                "gần nhất", "gan nhat", "lấy lần nhất", "lay lan nhat",
            )
            is_short_followup = len(str(last_content).split()) <= 12 and any(
                word in str(last_content).lower() for word in followup_words
            )
            has_explicit_code = re.search(code_pattern, str(last_content), re.I) is not None
            # A new material code can still be a continuation only when the
            # user signals that explicitly (for example, "thế còn mã X?").
            # A standalone question such as "mã X của khách hàng nào" starts
            # a new intent and must not inherit the prior date range.
            explicit_continuation = any(cue in normalized_last for cue in CONTINUATION_CUES)
            inherits_prior_request = is_short_followup and (
                not has_explicit_code or explicit_continuation
            )
            previous_user_content = next(
                (str(message.get("content", "")) for message in reversed(messages[:last_user_index])
                 if message.get("role") == "user"),
                "",
            )
            current_intents = request_intents(last_content)
            previous_intents = request_intents(previous_user_content)
            # “Thế còn mã khác?” has no new business intent, so it keeps the
            # active sales/stock question.  But “thế còn mã khác của khách
            # hàng nào?” changes to a customer lookup and is independent.
            if current_intents and previous_intents and not (current_intents & previous_intents):
                inherits_prior_request = False
            if not has_explicit_code and (
                is_short_followup or "cua no" in normalized_last or "ma nay" in normalized_last
            ):
                for previous in reversed(messages[:last_user_index]):
                    if previous.get("role") != "user":
                        continue
                    match = re.search(code_pattern, str(previous.get("content", "")), re.I)
                    if match:
                        messages[last_user_index] = {**messages[last_user_index], "content": f"{last_content}\nNgữ cảnh mã vật tư: {match.group(0)}"}
                        break
            has_date = bool(re.search(r"\b(?:\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b", str(last_content)))
            if inherits_prior_request and not has_date:
                for previous in reversed(messages[:last_user_index]):
                    if previous.get("role") != "user":
                        continue
                    previous_content = str(previous.get("content", ""))
                    if re.search(r"\b(?:\d{1,2}/\d{1,2}/\d{4}|\d{4}-\d{2}-\d{2})\b", previous_content):
                        messages[last_user_index] = {
                            **messages[last_user_index],
                            "content": f"{messages[last_user_index]['content']}\nĐiều kiện kế thừa từ câu hỏi trước: {previous_content}",
                        }
                        break
        tool_ids = body.setdefault("tool_ids", [])
        if "htmp_postgres_query" not in tool_ids:
            tool_ids.append("htmp_postgres_query")

        body["messages"] = add_or_update_system_message(
            "You are HTMP ERP. STRICT OUTPUT RULE: before the ask_erp tool result, emit ZERO natural-language text. "
            "For EVERY user request, make EXACTLY ONE native call to ask_erp FIRST. "
            "When the user sends multiple ERP questions in a list or ordinary sentences, pass the complete text in that single call: ask_erp detects separate questions and returns an independent result for each. "
            "If ask_erp returns status=batch_success, repeat rendered_answer VERBATIM and stop. "
            "After that call returns, answer immediately from its result; NEVER call ask_erp a second time in the same turn. "
            "Never preface a tool call with an explanation, plan, apology, confirmation request, or a statement that you will make a new ERP request. "
            "A new material code with a continuation cue such as 'thế còn mã X' keeps the prior request intent and its relevant filters. "
            "A standalone new question with a new intent, for example 'mã X của khách hàng nào', is independent: do not inherit its old date range or other filters. "
            "Do not mention a previous material code, date range, or question unless the latest user message explicitly refers to it. "
            "A short follow-up must inherit filters from the relevant prior ERP request and call ask_erp once. An explicit material code in the latest user message is a NEW identifier: it overrides every earlier material code, must be sent to ask_erp immediately, and must never trigger a clarification question. Each new user question or new condition requires a NEW database query; never "
            "reuse a previous tool result as the answer. Never invent table or column names "
            "and never ask the user for SQL. When a follow-up uses a reference such as 'mã này', "
            "include the resolved identifier and the relevant prior request in the ask_erp question. "
            "Treat ERP tool results as the source of truth; "
            "never say data is unavailable merely because RAG documents do not contain it. "
            "If ask_erp returns 'KẾT QUẢ ERP ĐÃ XÁC NHẬN', repeat that confirmed result "
            "VERBATIM and stop: add no interpretation, caveat, or commentary. Never replace it with a missing-data statement. "
            "For a price response, inspect summary.bao_gia_ncc_gan_nhat. When it is non-empty, you MUST state the supplier-quote price before VAT AND after VAT, its unit, effective dates, and approval status. Do not omit either VAT price merely because it equals the latest purchase-order price. Also label the purchase-order price as historic and the supplier quote as a quote; never call a quote an actual purchase. "
            "If the tool returns multiple transaction rows, do not choose one arbitrarily: state the matching rows and ask for a date, receipt, or warehouse if one row is needed. "
            "A follow-up such as 'gần nhất' or 'lấy lần nhất' means query ERP immediately using the inherited identifier; do not ask the user to repeat it. "
            "Answer the user in Vietnamese.",
            body.get("messages", []),
            append=True,
        )

        # Carry only an opaque request identifier across the customizable
        # retrieval boundary. Do not copy prompt, source text, auth headers,
        # user email, or credentials into metadata/events.
        request_id = __request__.headers.get("x-request-id") if __request__ else None
        if request_id:
            body.setdefault("metadata", {}).setdefault(
                "htmp_observability",
                {"request_id": request_id, "retrieval_profile": self.__class__.__module__},
            )

        # This profile is selected explicitly as ERP. Never inject internal
        # document context or fall back to RAG based on keyword inference.
        body.pop("files", None)
        body.setdefault("metadata", {}).pop("files", None)
        return body
