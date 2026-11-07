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

            explicit_anaphora = any(cue in normalized_last for cue in ("cua no", "ma nay", "vat tu nay", "kho nay"))
            if not has_explicit_code and not has_new_topic and (inherits_prior_request or explicit_anaphora):
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
            "QUY TẮC SỬ DỤNG CÔNG CỤ (NATIVE FUNCTION CALLING):\n"
            "Khi người dùng yêu cầu thông tin, bạn BẮT BUỘC gọi công cụ tương ứng phù hợp nhất:\n"
            "1. lookup_sales_price: Tra cứu giá bán, chính sách giá bán của mã hàng, sản phẩm hoặc linh kiện (ví dụ: '156279430', 'T1015910DA', 'QC7-5146-000').\n"
            "2. lookup_inventory_stock: Tra cứu số lượng hàng tồn kho theo mã vật tư hoặc tổng tồn tại từng kho cụ thể (ví dụ: 'KHOTP00', 'KHO-CXL', 'KHO-IN', 'KHONVL').\n"
            "3. lookup_sales_orders: Tra cứu đơn hàng bán (SO), tiến độ giao hàng hoặc lịch sử xuất bán (HDA).\n"
            "4. lookup_purchase_orders: Tra cứu lịch sử đặt mua hàng NCC (PO), giá mua vật tư.\n"
            "5. lookup_mold_and_mes: Tra cứu hồ sơ khuôn mẫu, tổng số shot dập, định mức bảo hành, máy ép MES (ví dụ: khuôn của 'QC7-5146-000' hoặc '14HI202').\n"
            "6. lookup_general_catalog: Tra cứu danh mục chung: mã nhân viên (ví dụ '4509' là anh Nguyễn Văn Trường), thông tin khách hàng, quy cách đóng gói (thùng/khay trong dmvt).\n"
            "7. ask_erp: Công cụ dự phòng cho các câu hỏi tổng hợp nhiều chỉ tiêu phức tạp không thuộc các công cụ trên.\n\n"
            "DỮ LIỆU THỜI GIAN VẬN HÀNH: Hệ thống ERP HTMP hiện đang vận hành trong năm 2026. Mọi mốc thời gian năm 2026 (ví dụ tháng 10/2026, ngày 29/10/2026, 06/11/2026...) là dữ liệu thực tế đang vận hành, TUYỆT ĐỐI KHÔNG coi là ngày tương lai.\n"
            "QUY TẮC PHẢN HỒI: Sau khi nhận được kết quả từ công cụ, hãy trả lời THẲNG VÀO TRỌNG TÂM câu hỏi, ngắn gọn, súc tích, dứt khoát đúng số liệu. Tuyệt đối KHÔNG xuất các câu rào đón hoặc độc thoại nội tâm. Khi câu hỏi yêu cầu danh sách hoặc so sánh, hãy trình bày bằng bảng Markdown đẹp mắt. Sau khi gọi công cụ xong, trả lời ngay và DỪNG LẠI.",
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

        # 1. Clean any raw references to "bảng phía trên", "bảng ở trên", "khung phía trên"
        patterns_to_remove = [
            r"(?:[^\.\n]*\b(?:bảng|khung|chi tiết)\s+(?:ở|phía|ở phía)?\s*trên[^\.\n]*[\.\n]?)",
            r"(?:[^\.\n]*\bxem thêm chi tiết trong bảng[^\.\n]*[\.\n]?)",
        ]
        for pat in patterns_to_remove:
            content = re.sub(pat, "", content, flags=re.I)

        # 2. Strip Chinese/Hanzi characters if any leaked
        if re.search(r"[\u4e00-\u9fff]", content):
            content = re.sub(r"[\u4e00-\u9fff]+(?:\s*[\(\uff08][^\)\uff09]+[\)\uff09])?", "", content)
            content = re.sub(r"^[：:\s]+", "", content)

        # 3. Clean up duplicate empty lines and whitespace
        content = re.sub(r"[ \t]+", " ", content)
        content = re.sub(r"\n{3,}", "\n\n", content).strip()
        last_msg["content"] = content
        return body
