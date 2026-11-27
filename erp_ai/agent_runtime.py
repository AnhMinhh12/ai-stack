"""Async runtime adapters; no credentials are returned or logged."""
import json
import os
import re
from pathlib import Path

from .agent import Limits, run_agent
from .agent_backend import ReportBackend
from .semantic_model import load_erp_config


def _extract_inline_tool_calls(message, tools):
    """Recover Qwen <tool_call> blocks if vLLM left them in message content."""
    if not tools or message.get("tool_calls"):
        return message
    content = message.get("content")
    if not isinstance(content, str) or "<tool_call>" not in content:
        return message
    allowed = {t["function"]["name"] for t in tools if isinstance(t, dict) and isinstance(t.get("function"), dict)}
    decoder = json.JSONDecoder()
    recovered = []
    for m in re.finditer(r"<tool_call>\s*", content):
        start = m.end()
        try:
            obj, _ = decoder.raw_decode(content, start)
        except ValueError:
            end_tag = content.find("</tool_call>", start)
            snippet = (content[start:end_tag] if end_tag != -1 else content[start:]).strip()
            try:
                obj, _ = decoder.raw_decode(snippet + "}", 0)
            except ValueError:
                continue
        if not isinstance(obj, dict):
            continue
        name = obj.get("name")
        arguments = obj.get("arguments")
        if not isinstance(name, str) or name not in allowed or arguments is None:
            continue
        arg_str = json.dumps(arguments, ensure_ascii=False) if isinstance(arguments, dict) else str(arguments)
        recovered.append({"id": f"call_inline_{len(recovered)}", "type": "function",
                          "function": {"name": name, "arguments": arg_str}})
    if recovered:
        message = dict(message, content=None, tool_calls=recovered)
    return message


class QwenClient:
    def __init__(self, client, model):
        self.client, self.model = client, model

    async def __call__(self, messages, tools):
        payload = {
            "model": self.model, "messages": messages,
            "temperature": 0, "max_tokens": 700, "stream": False
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
            payload["parallel_tool_calls"] = False
        response = await self.client.post("chat/completions", json=payload)
        response.raise_for_status()
        return _extract_inline_tool_calls(response.json()["choices"][0]["message"], tools)


def _resolve_dsn() -> str:
    dsn = os.getenv("HTMP_AGENT_DB_DSN", "").strip()
    if dsn:
        return dsn
    host = os.getenv("HTMP_DB_HOST", "").strip()
    user = os.getenv("HTMP_DB_USER", "").strip()
    password = os.getenv("HTMP_DB_PASSWORD", "")
    if not (host and user and password):
        return ""
    port = os.getenv("HTMP_DB_PORT", "5410").strip() or "5410"
    dbname = os.getenv("HTMP_DB_NAME", "3SERP_HTMP_DATA").strip() or "3SERP_HTMP_DATA"
    return f"host={host} port={port} dbname={dbname} user={user} password={password}"


async def query(sql, parameters, limits):
    import psycopg
    from psycopg.rows import dict_row
    dsn = _resolve_dsn()
    async with await psycopg.AsyncConnection.connect(dsn, connect_timeout=5, row_factory=dict_row) as conn:
        async with conn.cursor() as cur:
            await cur.execute("SET TRANSACTION READ ONLY")
            await cur.execute("SELECT set_config('statement_timeout', %s, true)", (str(min(10000, int(limits.seconds*1000))),))
            await cur.execute("SELECT set_config('lock_timeout', '1000', true)")
            await cur.execute(sql, parameters)
            return await cur.fetchmany(limits.rows + 1)


async def answer(question, user, history=(), on_status=None):
    import httpx
    if os.getenv("HTMP_AGENT_ENABLED") in ("disabled", "-1"):
        return {"status": "disabled", "answer": "Luồng ERP nhiều lượt chưa được bật."}
    dsn = _resolve_dsn()
    if not dsn:
        return {"status": "configuration_error", "answer": "Chưa cấu hình kết nối ERP staging chỉ đọc."}
    root = Path(os.environ.get("HTMP_AGENT_ROOT", "/app/backend" if Path("/app/backend/config/erp-agent.json").exists() else Path(__file__).resolve().parents[1]))
    config = load_erp_config(root)
    grants = json.loads(os.getenv("HTMP_AGENT_GRANTS", "{}"))
    if not grants:
        all_reports = [r["id"] for r in config.get("reports", [])]
        all_datasets = [
            key for key, value in config.get("semantic_contracts", {}).items()
            if isinstance(value, dict) and value.get("status") == "approved"
        ]
        shared_uid = os.getenv("HTMP_ERP_SHARED_USER_ID", "11")
        uid = int(shared_uid) if shared_uid.isdecimal() and int(shared_uid) > 0 else 11
        grants = {"*": {"erp_user_id": uid, "reports": all_reports, "semantic_datasets": all_datasets}}
    backend = ReportBackend(root, config, grants, query)
    if not backend.authorized(user):
        return {"status": "forbidden", "answer": "Chưa được cấp quyền cho báo cáo này."}
    base = os.getenv("HTMP_AGENT_MODEL_URL", "http://vllm:8000/v1/").rstrip("/") + "/"
    key = os.getenv("VLLM_API_KEY", "")
    limits_obj = Limits(**config["limits"])
    async with httpx.AsyncClient(base_url=base, headers={"Authorization": "Bearer " + key},
                                timeout=float(limits_obj.seconds), follow_redirects=False, trust_env=False) as client:
        return await run_agent(question, user=user, model=QwenClient(client, os.getenv("HTMP_AGENT_MODEL", "qwen2.5-14b")),
                               backend=backend, limits=limits_obj, history=history, on_status=on_status)
