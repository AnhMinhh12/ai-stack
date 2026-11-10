"""
title: HTMP ERP
author: HTMP Platform
version: 1.1.0
required_open_webui_version: 0.6.0
"""

"""Explicit ERP-only profile for the HTMP workspace model."""

import re
import unicodedata
from erp_ai.entities import extract_entities

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
            raw_content = str(messages[last_user_index].get("content") or "")
            clean_content = raw_content.strip()
            table_match = re.search(r"\|\s*`?([^`\|\n]+?)`?\s*\|", clean_content)
            if table_match and len(table_match.group(1).strip()) > 2:
                clean_content = table_match.group(1).strip()
            clean_content = re.sub(r"^```(?:markdown)?\s*", "", clean_content, flags=re.I)
            clean_content = re.sub(r"\s*```$", "", clean_content)
            clean_content = re.sub(r"^[`\|\s]+|[`\|\s]+$", "", clean_content).strip()
            if clean_content and clean_content != raw_content:
                messages[last_user_index]["content"] = clean_content
            last_content = clean_content
            normalized_last = re.sub(r"[^a-z0-9]+", " ", str(last_content).lower()).strip()
            # Do not cap the alphabetic prefix: valid ERP material codes such
            # as GCCKSC164 have six letters before their digits.  An explicit
            # code in the current turn must never be treated as a follow-up
            # referring to the previously remembered material.
            followup_words = (
                "đâu", "nào", "bao nhiêu", "thế", "còn", "thì sao",
                "khác", "tiếp theo", "tương tự",
                "gần nhất", "gan nhat", "lấy lần nhất", "lay lan nhat",
            )
            is_short_followup = len(str(last_content).split()) <= 12 and any(
                word in str(last_content).lower() for word in followup_words
            )
            has_explicit_code = bool(extract_entities(str(last_content))["ma_vt"])
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
            new_topic_cues = (
                "model", "nha cung cap", "ncc", "khuon", "mold",
                "toan bo", "tat ca", "he thong", "danh sach", "danh muc",
                "co bao nhieu", "tong so", "nhua abs", "goc nhua",
                "file excel", "xuat excel", "bao nhieu ma"
            )
            has_new_topic = any(cue in normalized_last for cue in new_topic_cues)
            if has_new_topic:
                inherits_prior_request = False

            explicit_anaphora = any(cue in normalized_last for cue in (
                "cua no", "ma nay", "ma do", "ma tren", "ma vua roi", "ma vua tra",
                "vat tu nay", "vat tu do", "hang nay", "san pham nay",
                "khuon nay", "kho nay", "don nay", "po nay"
            ))
            if not has_explicit_code and (explicit_anaphora or (not has_new_topic and inherits_prior_request)):
                for previous in reversed(messages[:last_user_index]):
                    if previous.get("role") != "user":
                        continue
                    previous_code = extract_entities(str(previous.get("content", "")))["ma_vt"]
                    if previous_code:
                        messages[last_user_index] = {**messages[last_user_index], "content": f"{last_content}\nNgữ cảnh mã vật tư: {previous_code}"}
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
            "Bạn là trợ lý AI HTMP ERP chuyên trách tra cứu dữ liệu nhà máy HTMP. BẮT BUỘC TRẢ LỜI 100% BẰNG TIẾNG VIỆT. TUYỆT ĐỐI CẤM SỬ DỤNG TIẾNG TRUNG HOẶC CHỮ HÁN.\n"
            "QUY TẮC SỬ DỤNG CÔNG CỤ (ENTERPRISE UNIFIED GATEWAY):\n"
            "Khi người dùng yêu cầu tra cứu bất kỳ thông tin nào về nhà máy và dữ liệu ERP/MES (Kho, Bán hàng, Mua hàng, Kế toán, MES sản xuất, BOM, QC, Khuôn mẫu, Danh mục), bạn BẮT BUỘC gọi công cụ duy nhất:\n"
            "-> query_htmp_erp: Truyền nguyên văn câu hỏi của người dùng vào tham số 'question'.\n\n"
            "DỮ LIỆU THỜI GIAN VẬN HÀNH: Hệ thống ERP HTMP hiện đang vận hành trong năm 2026. Mọi mốc thời gian năm 2026 (ví dụ tháng 10/2026, ngày 29/10/2026, 06/11/2026...) là dữ liệu thực tế đang vận hành, TUYỆT ĐỐI KHÔNG coi là ngày tương lai.\n"
            "QUY TẮC PHẢN HỒI (TUÂN THỦ TUYỆT ĐỐI):\n"
            "- Trả lời THẲNG VÀO TRỌNG TÂM câu hỏi, ngắn gọn, súc tích, dứt khoát đúng số liệu.\n"
            "- TUYỆT ĐỐI KHÔNG xuất các thẻ kỹ thuật như <tool_call>, <think>, ```json, arguments, hoặc câu độc thoại như 'Hãy đợi tôi một chút', 'Tôi sẽ tra cứu thêm'.\n"
            "- Hiển thị nguyên vẹn bảng Markdown và các chỉ tiêu phân tích số liệu mà công cụ đã tính toán và trả về. Sau khi nhận kết quả từ công cụ, tổng hợp trả lời ngay và DỪNG LẠI.",
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

        # Force tool_choice on user turn to ensure ERP tool execution
        # and prevent hallucinations or premature plain-text responses.
        # Once a tool result is received (role == 'tool'), strictly set tool_choice="none"
        # so the model is forced to synthesize the final answer text immediately and never loop.
        non_system_messages = [m for m in body.get("messages", []) if m.get("role") != "system"]
        last_msg = non_system_messages[-1] if non_system_messages else None
        if last_msg and last_msg.get("role") == "tool":
            body["tool_choice"] = "none"
        elif last_msg and last_msg.get("role") == "user" and len(non_system_messages) >= 2 and non_system_messages[-2].get("role") == "tool":
            body["tool_choice"] = "none"
        elif last_msg and last_msg.get("role") == "user":
            body["tool_choice"] = "auto"
        else:
            body["tool_choice"] = "none"

        return body

    async def outlet(
        self, body, __request__, __user__, __model__=None, __event_emitter__=None
    ):
        messages = body.get("messages", [])
        if not messages:
            return body
        last_msg = messages[-1]
        content = str(last_msg.get("content") or "")
        if not content:
            return body

        # 1. Clean leaked raw <tool_call>, <think>, or code block tool artifacts
        content = re.sub(r"<tool_call>[\s\S]*?</tool_call>", "", content)
        content = re.sub(r"<tool_call>[\s\S]*$", "", content)
        content = re.sub(r"```json\s*\{\s*\"name\":\s*\"(?:lookup_|query_|ask_)[^\"]+\"[\s\S]*?```", "", content)
        content = re.sub(r"<think>[\s\S]*?</think>", "", content)
        content = re.sub(r"<thought>[\s\S]*?</thought>", "", content)

        # 2. Clean monologue filler sentences and raw table references
        monologues = [
            r"(?:[^\.\n]*\b(?:Tôi sẽ tra cứu thêm|Hãy đợi tôi một chút|đợi tôi một lát|chờ tôi một chút|đang tra cứu thêm)[^\.\n]*[\.\n]?)",
            r"(?:[^\.\n]*\bDữ liệu báo cáo[^\.\n]*không trực tiếp so sánh[^\.\n]*[\.\n]?)",
            r"(?:[^\.\n]*\b(?:bảng|khung|chi tiết)\s+(?:ở|phía|ở phía)?\s*trên[^\.\n]*[\.\n]?)",
            r"(?:[^\.\n]*\bxem thêm chi tiết trong bảng[^\.\n]*[\.\n]?)",
        ]
        for pat in monologues:
            content = re.sub(pat, "", content, flags=re.I)

        # 3. Strip Chinese/Hanzi characters if any leaked
        if re.search(r"[\u4e00-\u9fff]", content):
            content = re.sub(r"[\u4e00-\u9fff]+(?:\s*[\(\uff08][^\)\uff09]+[\)\uff09])?", "", content)
            content = re.sub(r"^[：:\s]+", "", content)

        # 4. Clean up duplicate empty lines and whitespace
        content = re.sub(r"[ \t]+", " ", content)
        content = re.sub(r"\n{3,}", "\n\n", content).strip()

        # If content became empty because model only emitted a tool call,
        # fallback to the last tool's text result so user sees the report!
        if not content:
            for prev in reversed(messages[:-1]):
                if prev.get("role") == "tool":
                    prev_text = str(prev.get("content") or "")
                    if prev_text:
                        content = prev_text
                        break

        last_msg["content"] = content
        return body
