"""Async runtime adapters; no credentials are returned or logged."""
import json
import os
from pathlib import Path

from .agent import Limits, run_agent
from .agent_backend import ReportBackend


class QwenClient:
    def __init__(self, client, model):
        self.client, self.model = client, model

    async def __call__(self, messages, tools):
        response = await self.client.post("chat/completions", json={
            "model": self.model, "messages": messages, "tools": tools,
            "tool_choice": "auto", "parallel_tool_calls": False, "temperature": 0, "max_tokens": 1500, "stream": False})
        response.raise_for_status()
        return response.json()["choices"][0]["message"]


async def query(sql, parameters, limits):
    import psycopg
    from psycopg.rows import dict_row
    # Dedicated staging DSN; intentionally no fallback to production DB credentials.
    dsn = os.environ["HTMP_AGENT_DB_DSN"]
    async with await psycopg.AsyncConnection.connect(dsn, connect_timeout=5, row_factory=dict_row) as conn:
        async with conn.cursor() as cur:
            await cur.execute("SET TRANSACTION READ ONLY")
            await cur.execute("SELECT set_config('statement_timeout', %s, true)", (str(min(10000, int(limits.seconds*1000))),))
            await cur.execute("SELECT set_config('lock_timeout', '1000', true)")
            await cur.execute(sql, parameters)
            return await cur.fetchmany(limits.rows + 1)


async def answer(question, user, history=(), on_status=None):
    import httpx
    if os.getenv("HTMP_AGENT_ENABLED") != "1":
        return {"status": "disabled", "answer": "Luồng ERP nhiều lượt chưa được bật."}
    if not os.getenv("HTMP_AGENT_DB_DSN"):
        return {"status": "configuration_error", "answer": "Chưa cấu hình kết nối ERP staging chỉ đọc."}
    root = Path(os.environ["HTMP_AGENT_ROOT"])
    config = json.loads((root / "config/erp-agent.json").read_text())
    grants = json.loads(os.getenv("HTMP_AGENT_GRANTS", "{}"))
    backend = ReportBackend(root, config, grants, query)
    if not backend.authorized(user):
        return {"status": "forbidden", "answer": "Chưa được cấp quyền cho báo cáo này."}
    base = os.getenv("HTMP_AGENT_MODEL_URL", "http://vllm:8000/v1/").rstrip("/") + "/"
    key = os.getenv("VLLM_API_KEY", "")
    async with httpx.AsyncClient(base_url=base, headers={"Authorization": "Bearer " + key},
                                timeout=30, follow_redirects=False, trust_env=False) as client:
        return await run_agent(question, user=user, model=QwenClient(client, os.getenv("HTMP_AGENT_MODEL", "qwen2.5-14b")),
                               backend=backend, limits=Limits(**config["limits"]), history=history, on_status=on_status)
