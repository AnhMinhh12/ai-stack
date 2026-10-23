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
            last_content = messages[last_user_index].get("content")
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
            if not has_explicit_code and (
                is_short_followup or "cua no" in normalized_last or "ma nay" in normalized_last
            ):
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
            "Bạn là HTMP ERP. QUY TẮC ĐẦU RA BẮT BUỘC: trước khi nhận được kết quả từ công cụ ask_erp, TUYỆT ĐỐI KHÔNG xuất bất kỳ văn bản tự nhiên nào. "
            "Đối với MỌI yêu cầu của người dùng, BẮT BUỘC thực hiện ĐÚNG MỘT lệnh gọi công cụ ask_erp ĐẦU TIÊN. "
            "Khi người dùng gửi nhiều câu hỏi ERP trong danh sách hoặc các câu văn thông thường, hãy chuyển toàn bộ nội dung trong một lệnh gọi duy nhất: ask_erp sẽ tự nhận diện từng câu hỏi riêng biệt và trả về kết quả độc lập cho từng câu. "
            "Nếu ask_erp trả về status=batch_success, hãy lặp lại NGUYÊN VĂN rendered_answer và dừng lại. "
            "Sau khi lệnh gọi hoàn tất, hãy trả lời ngay từ kết quả đó; TUYỆT ĐỐI KHÔNG gọi ask_erp lần thứ hai trong cùng một lượt. "
            "Tuyệt đối không mở đầu lệnh gọi công cụ bằng lời giải thích, kế hoạch, xin lỗi, yêu cầu xác nhận hoặc tuyên bố sẽ thực hiện yêu cầu ERP mới. "
            "Một mã vật tư mới đi kèm từ nối tiếp như 'thế còn mã X' sẽ giữ nguyên ý định yêu cầu trước và các bộ lọc liên quan. "
            "Một câu hỏi độc lập mới với ý định mới, ví dụ 'mã X của khách hàng nào', là hoàn toàn độc lập: không kế thừa khoảng ngày cũ hoặc các bộ lọc trước đó. "
            "Không nhắc lại mã vật tư, khoảng ngày hoặc câu hỏi trước đó trừ khi tin nhắn mới nhất của người dùng đề cập rõ ràng đến chúng. "
            "Một câu hỏi ngắn nối tiếp phải kế thừa bộ lọc từ yêu cầu ERP liên quan trước đó và gọi ask_erp một lần. Một mã vật tư rõ ràng trong tin nhắn mới nhất là một mã định danh MỚI: nó ghi đè lên mọi mã vật tư trước đó, phải được gửi đến ask_erp ngay lập tức và tuyệt đối không bao giờ kích hoạt câu hỏi làm rõ. Mỗi câu hỏi mới hoặc điều kiện mới của người dùng đều cần một truy vấn cơ sở dữ liệu MỚI; tuyệt đối không "
            "tái sử dụng kết quả công cụ trước làm câu trả lời. Không tự bịa tên bảng hoặc tên cột "
            "và không bao giờ hỏi người dùng câu lệnh SQL. Khi câu hỏi nối tiếp sử dụng tham chiếu như 'mã này', "
            "hãy đưa mã định danh đã xác định và yêu cầu liên quan trước đó vào câu hỏi ask_erp. "
            "Coi kết quả từ công cụ ERP là nguồn sự thật duy nhất; "
            "không bao giờ nói dữ liệu không khả dụng chỉ vì tài liệu RAG không chứa dữ liệu đó. "
            "Nếu ask_erp trả về 'KẾT QUẢ ERP ĐÃ XÁC NHẬN', hãy lặp lại kết quả đã xác nhận đó "
            "NGUYÊN VĂN và dừng lại: không thêm diễn giải, cảnh báo hoặc bình luận. Tuyệt đối không thay thế bằng câu thông báo thiếu dữ liệu. "
            "Đối với phản hồi về giá, hãy kiểm tra summary.bao_gia_ncc_gan_nhat. Khi trường này không rỗng, bạn BẮT BUỘC phải nêu rõ giá báo của nhà cung cấp trước VAT VÀ sau VAT, đơn vị tính, ngày hiệu lực và trạng thái phê duyệt. Không bỏ sót bất kỳ mức giá VAT nào chỉ vì nó bằng giá đơn mua gần nhất. Đồng thời hãy gọi giá đơn mua là giá lịch sử và báo giá nhà cung cấp là báo giá; không bao giờ gọi báo giá là đơn mua thực tế. "
            "Nếu công cụ trả về nhiều dòng giao dịch, không tự chọn một dòng tùy ý: hãy nêu các dòng khớp và hỏi thêm ngày, số phiếu hoặc kho nếu chỉ cần một dòng. "
            "Câu hỏi nối tiếp như 'gần nhất' hoặc 'lấy lần nhất' có nghĩa là truy vấn ERP ngay lập tức bằng mã định danh đã kế thừa; không yêu cầu người dùng lặp lại. "
            "Trả lời người dùng bằng tiếng Việt.",
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
