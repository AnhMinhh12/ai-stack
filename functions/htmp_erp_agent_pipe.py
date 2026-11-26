"""
title: ERP nhiều lượt (Pipe trực tiếp)
author: HTMP Platform
version: 0.2.0
required_open_webui_version: 0.6.0
"""
from __future__ import annotations

import os
import re
from typing import Any

from erp_ai.agent_runtime import answer
from erp_ai.export_files import build_downloads, requested_formats
from erp_ai.rich_ui import render_erp_embed


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return " ".join(parts).strip()
    return ""


def extract_question_and_history(messages: list[dict[str, Any]] | None) -> tuple[str, list[dict[str, str]]]:
    """Extract the latest user question and prior user/assistant turns without outer LLM rewriting."""
    clean: list[dict[str, str]] = []
    for msg in messages or []:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        if role not in ("user", "assistant"):
            continue
        text = _content_to_text(msg.get("content"))
        if text:
            clean.append({"role": role, "content": text})
    for idx in range(len(clean) - 1, -1, -1):
        if clean[idx]["role"] == "user":
            return clean[idx]["content"], clean[:idx]
    return "", clean


def sanitize_reply_text(text: str) -> str:
    """Strip leaked tool tags or CJK characters as defense-in-depth."""
    cleaned = str(text or "")
    if not cleaned:
        return ""
    cleaned = re.sub(r"<tool_call>[\s\S]*?</tool_call>", "", cleaned)
    cleaned = re.sub(r"<tool_call>[\s\S]*$", "", cleaned)
    cleaned = re.sub(r"<(?:think|thought)>[\s\S]*?</(?:think|thought)>", "", cleaned)
    if re.search(r"[\u4e00-\u9fff]", cleaned):
        cleaned = re.sub(r"[^.!?\n]*[\u4e00-\u9fff][^.!?\n]*(?:[.!?：:]+|\s*)", "", cleaned)
        cleaned = re.sub(r"^[：:,\s]+", "", cleaned)
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
    return cleaned


def format_pipe_reply(result: dict[str, Any], *, has_embed: bool) -> str:
    """Produce a deterministic Vietnamese reply directly from verified backend results."""
    status = result.get("status", "")
    summary = sanitize_reply_text(result.get("answer") or "")
    if has_embed:
        if status == "answered":
            return summary or "Dữ liệu tra cứu chi tiết đã được hiển thị trong bảng ở trên."
        if status == "partial":
            return summary or "Bảng kết quả đã hiển thị ở trên; dữ liệu chưa đầy đủ do vượt giới hạn hiển thị."
        return summary or "Kết quả tra cứu đã được hiển thị ở trên."
    text = sanitize_reply_text(result.get("display_markdown") or summary)
    return text or "Chưa đủ dữ liệu để trả lời."


class Pipe:
    async def _run_background_task(self, body: dict[str, Any]) -> str:
        """Handle Open WebUI title/tag/follow-up tasks via vLLM without ERP tools."""
        import httpx

        base = os.getenv("HTMP_AGENT_MODEL_URL", "http://vllm:8000/v1/").rstrip("/") + "/"
        key = os.getenv("VLLM_API_KEY", "")
        model = os.getenv("HTMP_AGENT_MODEL", "qwen2.5-14b")
        payload = {
            "model": model,
            "messages": body.get("messages") or [],
            "temperature": 0,
            "max_tokens": 256,
            "stream": False,
        }
        try:
            async with httpx.AsyncClient(
                base_url=base,
                headers={"Authorization": "Bearer " + key},
                timeout=15.0,
                follow_redirects=False,
                trust_env=False,
            ) as client:
                resp = await client.post("chat/completions", json=payload)
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"].get("content") or ""
                return sanitize_reply_text(content)
        except Exception:
            return ""

    async def pipe(
        self,
        body: dict[str, Any],
        __user__: dict[str, Any] | None = None,
        __event_emitter__=None,
        __task__=None,
        __metadata__: dict[str, Any] | None = None,
    ) -> str:
        if __task__:
            return await self._run_background_task(body)

        async def on_status(msg: str, done: bool = False):
            if __event_emitter__:
                await __event_emitter__({
                    "type": "status",
                    "data": {"description": msg, "done": done},
                })

        question, history = extract_question_and_history(body.get("messages"))
        if not question:
            return "Vui lòng nhập câu hỏi cần tra cứu ERP."

        await on_status("Đang phân tích câu hỏi và tra cứu ERP...")
        result = await answer(question, __user__, history, on_status=on_status)
        await on_status(f"Hoàn tất ({result.get('status', 'answered')})", done=True)

        downloads = []
        if result.get("status") in ("answered", "partial") and any(
            block.get("type") == "table" for block in result.get("blocks", [])
        ):
            try:
                downloads = build_downloads(result["blocks"], requested_formats(question))
            except Exception:
                result.setdefault("blocks", []).append({
                    "type": "warning",
                    "text": "Không thể tạo file tải xuống cho kết quả này.",
                    "source_ids": [],
                })

        html = render_erp_embed(result, downloads)
        emitted_embed = bool(html and __event_emitter__)
        if emitted_embed:
            await __event_emitter__({
                "type": "embeds",
                "data": {"embeds": [html]},
            })

        return format_pipe_reply(result, has_embed=emitted_embed)
