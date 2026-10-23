"""
title: ERP nhiều lượt (staging)
author: HTMP Platform
version: 0.1.0
required_open_webui_version: 0.6.0
"""
import json
from fastapi.responses import HTMLResponse
from erp_ai.agent_runtime import answer
from erp_ai.export_files import build_downloads, requested_formats
from erp_ai.rich_ui import render_erp_embed


class Tools:
    async def ask_erp_agent(self, question: str, __user__: dict = None, __messages__: list = None, __event_emitter__ = None):
        """Tra cứu ERP nhiều lượt trong phạm vi được cấp; Rich UI chỉ chứa dữ liệu đã xác minh."""
        async def on_status(msg):
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": msg, "done": False}
                })

        await on_status("Đang phân tích câu hỏi và tra cứu ERP...")
        # Both identity and history are injected server-side, absent from model arguments.
        history = [m for m in (__messages__ or []) if m.get("role") in ("user", "assistant")]
        if history and history[-1].get("role") == "user":
            history = history[:-1]
        result = await answer(question, __user__, history, on_status=on_status)
        if __event_emitter__:
            await __event_emitter__({
                "type": "status",
                "data": {"description": f"Hoàn tất ({result.get('status', 'answered')})", "done": True}
            })
        downloads = []
        if result.get("status") == "answered" and any(block.get("type") == "table" for block in result.get("blocks", [])):
            try:
                downloads = build_downloads(result["blocks"], requested_formats(question))
            except Exception:
                result["blocks"].append({"type": "warning", "text": "Không thể tạo file tải xuống cho kết quả này.", "source_ids": []})
        html = render_erp_embed(result, downloads)
        if html:
            has_chart = any(block.get("type") == "chart" for block in result.get("blocks", []))
            complete = result.get("status") == "answered"
            context = {"status": result.get("status"), "result_displayed": complete,
                       "partial_data_displayed": not complete,
                       "has_chart": has_chart,
                       "message": ("Kết quả đã hiển thị trong Rich UI. Chỉ trả đúng câu: Kết quả tra cứu ở trên."
                                   if complete else "Tra cứu chưa hoàn tất. Rich UI chỉ hiển thị dữ liệu đã xác minh; phải báo rõ lỗi, không xác nhận đã hoàn thành báo cáo.")}
            return HTMLResponse(content=html, headers={"Content-Disposition": "inline"}), context
        return result.get("display_markdown") or result.get("answer") or "Chưa đủ dữ liệu để trả lời."
