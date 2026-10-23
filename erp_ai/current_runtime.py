"""Multi-step read-only ERP lookup for the active HTMP ERP model."""
from __future__ import annotations

import json
import os
import re
from datetime import date, datetime
from pathlib import Path

from .agent import Limits, run_agent
from .agent_backend import ReportBackend
from .agent_runtime import QwenClient


def _reference_date(question: str) -> str:
    """Use a stated date, or the server date for current/undated questions."""
    matches = re.findall(r"\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{4}-\d{2}-\d{2}\b", question)
    if not matches:
        return date.today().isoformat()
    value = matches[-1]
    try:
        return datetime.strptime(value, "%d/%m/%Y" if "/" in value else "%Y-%m-%d").date().isoformat()
    except ValueError:
        return date.today().isoformat()


class CurrentReportBackend(ReportBackend):
    def __init__(self, root, config, grants, db, question):
        super().__init__(root, config, grants, db)
        self.reference_date = _reference_date(question)

    def validate(self, name, args):
        if name in {"query_price_list", "query_bom_structure", "query_inventory_balance", "query_inventory_by_warehouse",
                    "query_forecast_po", "query_packaging_spec", "query_mold_profile",
                    "query_mold_label_stock", "query_qc_status"} and "date_as_of" in args:
            args["date_as_of"] = self.reference_date
        return super().validate(name, args)


async def _read_only_query(sql, params, limits):
    import psycopg
    from psycopg.rows import dict_row

    settings = dict(host=os.environ["HTMP_DB_HOST"], port=os.getenv("HTMP_DB_PORT", "5410"),
                    dbname=os.environ["HTMP_DB_NAME"], user=os.environ["HTMP_DB_USER"],
                    password=os.environ["HTMP_DB_PASSWORD"], connect_timeout=5,
                    row_factory=dict_row)
    async with await psycopg.AsyncConnection.connect(**settings) as connection:
        await connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
        await connection.execute("SET LOCAL statement_timeout='15s'")
        await connection.execute("SET LOCAL lock_timeout='1s'")
        cursor = await connection.execute(sql, params)
        return await cursor.fetchmany(limits.rows + 1)


async def answer_current(question, erp_user_id, history=(), on_status=None):
    """Run the reviewed report allowlist with the server-resolved ERP identity."""
    if not isinstance(erp_user_id, int) or erp_user_id <= 0:
        return {"status": "forbidden", "answer": "Chưa có quyền tra cứu ERP cho phiên này."}
    import httpx

    root = Path(os.getenv("HTMP_AGENT_ROOT", "/app/backend"))
    config = json.loads((root / "config/erp-agent.json").read_text())
    user = {"id": "current-erp-request"}
    grants = {user["id"]: {"erp_user_id": erp_user_id,
                           "reports": [report["id"] for report in config["reports"]]}}
    backend = CurrentReportBackend(root, config, grants, _read_only_query, question)
    urls = [part.strip() for part in (os.getenv("OPENAI_API_BASE_URLS") or "http://vllm:8000/v1").replace(";", ",").split(",") if part.strip()]
    base_url = urls[0].rstrip("/") + "/"
    keys = [part.strip() for part in (os.getenv("OPENAI_API_KEYS") or os.getenv("VLLM_API_KEY") or "").replace(";", ",").split(",") if part.strip()]
    key = keys[0] if keys else ""
    async with httpx.AsyncClient(base_url=base_url, headers={"Authorization": "Bearer " + key},
                                 timeout=30, follow_redirects=False, trust_env=False) as client:
        return await run_agent(question, user=user, model=QwenClient(client, os.getenv("HTMP_AGENT_MODEL", "qwen2.5-14b")),
                               backend=backend, limits=Limits(**config["limits"]), history=history,
                               on_status=on_status)
