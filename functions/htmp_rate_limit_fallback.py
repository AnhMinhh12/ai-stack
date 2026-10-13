"""
title: HTMP Rate Limit Fallback
author: HTMP Platform
version: 1.0.0
required_open_webui_version: 0.6.0
"""

"""Filter to catch empty or rate-limited responses and display a friendly notification."""


class Filter:
    async def outlet(
        self, body, __user__=None, __model__=None, __event_emitter__=None, **kwargs
    ):
        messages = body.get("messages", [])
        if not messages:
            return body

        last_message = messages[-1]
        if last_message.get("role") == "assistant":
            content = last_message.get("content")
            # Check if assistant response is empty or contains upstream rate-limit errors
            is_empty = content is None or (isinstance(content, str) and not content.strip())
            is_quota_error = isinstance(content, str) and any(
                err in content.lower()
                for err in ("rate limit", "429", "quota exceeded", "resource_exhausted", "too many requests")
            )

            if is_empty or is_quota_error:
                model_name = (__model__ or {}).get("name") or (__model__ or {}).get("id") or "Model này"
                fallback_text = (
                    f"⚠️ **Thông báo**: {model_name} hiện đã **hết lượt yêu cầu** (Rate Limit / Quota Exceeded) "
                    "hoặc gặp sự cố kết nối tới máy chủ AI ngoài.\n\n"
                    "👉 Bạn vui lòng:\n"
                    "- Chuyển sang chế độ **Nhanh** hoặc **Kỹ** để tiếp tục sử dụng miễn phí không giới hạn.\n"
                    "- Hoặc đổi sang model khác còn lượt (ví dụ: **Gemini 3.1 Flash Lite**)."
                )
                last_message["content"] = fallback_text

                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "chat:outlet",
                            "data": {"messages": messages},
                        }
                    )

        return body
