"""
title: HTMP ERP
author: HTMP Platform
version: 1.1.0
required_open_webui_version: 0.6.0
"""

"""Explicit ERP-only profile for the HTMP workspace model."""

import re

from open_webui.utils.middleware import add_or_update_system_message
from open_webui.utils.misc import get_last_user_message


class Filter:
    async def inlet(
        self, body, __request__, __user__, __model__=None, __event_emitter__=None
    ):
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
                "gần nhất", "gan nhat", "lấy lần nhất", "lay lan nhat",
            )
            is_short_followup = len(str(last_content).split()) <= 12 and any(
                word in str(last_content).lower() for word in followup_words
            )
            if not re.search(code_pattern, str(last_content), re.I) and (
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
            if is_short_followup and not has_date:
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
            "You are HTMP ERP. For EVERY user request, make EXACTLY ONE native call to ask_erp FIRST. "
            "After that call returns, answer immediately from its result; NEVER call ask_erp a second time in the same turn. "
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
