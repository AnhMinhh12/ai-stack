"""
title: HTMP Technical RAG
author: HTMP Platform
version: 1.0.0
required_open_webui_version: 0.6.0
"""

"""Per-model hybrid RAG profile for the HTMP knowledge base.

This filter runs only when attached to the HTMP Kỹ workspace model. It
uses access-checked hybrid retrieval and reranking before injecting the
resulting context.
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
            "For every question about ERP data, warehouses, inventory, material/product "
            "codes (including ma_vt), orders, or records: you MUST use the PostgreSQL "
            "ERP tools before answering. For a material code or warehouse question, call "
            "find_material_by_code or find_materials_in_warehouse FIRST; never invent "
            "table or column names. Use get_erp_schema/query_erp_database only for other "
            "questions after schema lookup. Treat ERP tool results as the "
            "source of truth; never say data is unavailable merely because the RAG "
            "documents do not contain it. Answer the user in Vietnamese.",
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
                        "description": "Đang tra cứu kỹ tài liệu nội bộ",
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
            k=10,
            reranking_function=(
                (lambda query, documents: __request__.app.state.RERANKING_FUNCTION(
                    query, documents, user=user
                ))
                if __request__.app.state.RERANKING_FUNCTION
                else None
            ),
            k_reranker=5,
            r=0.3,
            hybrid_bm25_weight=0.5,
            hybrid_search=True,
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
                        "description": "Đã tra cứu kỹ tài liệu nội bộ",
                        "done": True,
                    },
                }
            )

        return body
