"""
title: HTMP Fast RAG
author: HTMP Platform
version: 1.1.0
required_open_webui_version: 0.6.0
"""

"""Per-model vector-only RAG profile for the HTMP knowledge base.

This filter runs only when attached to the HTMP Nhanh workspace model.  It
uses Open WebUI's access-checked retrieval helper, injects the resulting
context with the platform RAG template, then removes file attachments so the
global hybrid/reranker path cannot run a second time.
"""

from open_webui.models.users import UserModel
from open_webui.retrieval.utils import get_sources_from_items
from open_webui.utils.middleware import add_or_update_system_message, apply_source_context_to_messages
from open_webui.utils.misc import get_last_user_message


class Filter:
    async def inlet(
        self, body, __request__, __user__, __model__=None, __event_emitter__=None
    ):
        # Regular Open WebUI chats do not inherit a model's toolIds. Attach the
        # read-only ERP tool before middleware resolves tools for this request.
        tool_ids = body.setdefault("tool_ids", [])
        if "htmp_postgres_query" not in tool_ids:
            tool_ids.append("htmp_postgres_query")

        body["messages"] = add_or_update_system_message(
            "For every ERP data question (warehouse, inventory, material/product codes, "
            "ma_vt, ma_lo, ma_vi_tri, dates, orders, or records), call ask_erp FIRST. "
            "Each new user question or new condition requires a NEW database query; never "
            "reuse a previous tool result as the answer. Never invent table or column names "
            "and never ask the user for SQL. Treat ERP tool results as the source of truth; "
            "never say data is unavailable merely because RAG documents do not contain it. "
            "Answer the user in Vietnamese.",
            body.get("messages", []),
            append=True,
        )

        user = UserModel(**__user__)
        files = body.get("files") or []
        model_meta = ((__model__ or {}).get("info") or {}).get("meta") or {}
        model_knowledge = model_meta.get("knowledge") or []
        prompt = get_last_user_message(body.get("messages", [])) or ""

        # Carry only an opaque request identifier across the customizable
        # retrieval boundary. Do not copy prompt, source text, auth headers,
        # user email, or credentials into metadata/events.
        request_id = __request__.headers.get("x-request-id") if __request__ else None
        if request_id:
            body.setdefault("metadata", {}).setdefault(
                "htmp_observability",
                {"request_id": request_id, "retrieval_profile": self.__class__.__module__},
            )

        # ERP questions are answered from PostgreSQL. Skipping document RAG for
        # these avoids consuming the model context with unrelated long manuals.
        prompt_lower = prompt.lower()
        erp_markers = ("ma_vt", "mã vt", "mã vật tư", "ma kho", "mã kho", "kho ", "tồn kho", "ton kho")
        looks_like_erp_data = any(marker in prompt_lower for marker in erp_markers)
        if looks_like_erp_data:
            # Legacy tool calling attaches model Knowledge before filter inlets.
            # Clear it here so the generic RAG handler cannot inject manuals.
            body.pop("files", None)
            body.setdefault("metadata", {}).pop("files", None)
            return body

        # Native tool calling keeps model Knowledge out of body["files"].
        # Prefer explicit chat attachments when supplied; otherwise retrieve
        # from every Knowledge Base attached to this model.
        items = files or model_knowledge

        if not items or not prompt.strip():
            return body

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "action": "knowledge_search",
                        "description": "Đang tra cứu nhanh tài liệu nội bộ",
                        "done": False,
                    },
                }
            )

        sources = await get_sources_from_items(
            request=None,
            items=items,
            queries=[prompt],
            embedding_function=lambda query, prefix: __request__.app.state.EMBEDDING_FUNCTION(
                query, prefix=prefix, user=user
            ),
            k=6,
            reranking_function=None,
            k_reranker=0,
            r=0.0,
            hybrid_bm25_weight=0.0,
            hybrid_search=False,
            user=user,
        )

        if sources:
            body["messages"] = await apply_source_context_to_messages(
                __request__, body.get("messages", []), sources, prompt
            )
            body.setdefault("metadata", {})["sources"] = sources

        # The standard handler is global-config driven.  Removing the consumed
        # attachments prevents it from launching a second hybrid/rerank request.
        body.pop("files", None)
        body.setdefault("metadata", {}).pop("files", None)

        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "action": "knowledge_search",
                        "description": "Đã tra cứu nhanh tài liệu nội bộ",
                        "done": True,
                    },
                }
            )

        return body
