#!/usr/bin/env python3
"""Index governed semantic contracts + 3SERP UI metadata into Qdrant using local BAAI/bge-m3."""
from __future__ import annotations

import argparse
import hashlib
import os
import sys
import uuid
from pathlib import Path

ROOT = Path(os.environ.get("HTMP_AGENT_ROOT", Path(__file__).resolve().parents[1])).resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from erp_ai.semantic_model import load_erp_config
from erp_ai.semantic_retriever import catalog_documents_for_indexing, encode_texts_bge_m3


def sync_qdrant_catalog(
    *,
    root: Path = ROOT,
    qdrant_uri: str | None = None,
    collection: str = "htmp_erp_semantic_catalog",
    recreate: bool = False,
) -> dict[str, int | str]:
    """Embed all approved semantic contracts with local BGE-M3 and upsert into Qdrant."""
    import httpx

    uri = (qdrant_uri or os.getenv("QDRANT_URI") or "http://qdrant:6333").rstrip("/")
    config = load_erp_config(root)
    docs = catalog_documents_for_indexing(config)
    if not docs:
        raise RuntimeError("No approved semantic contracts found to index")

    vectors = encode_texts_bge_m3([doc["text"] for doc in docs])
    if len(vectors) != len(docs) or not vectors[0]:
        raise RuntimeError(
            "Failed to encode semantic contracts using local BAAI/bge-m3 snapshot "
            "(verify HTMP_SEMANTIC_EMBEDDING_MODEL_PATH or /app/backend/data/cache/embedding/models)"
        )
    dim = len(vectors[0])
    headers = {}
    api_key = os.getenv("QDRANT_API_KEY", "").strip()
    if api_key:
        headers["api-key"] = api_key

    with httpx.Client(timeout=30.0, trust_env=False) as client:
        if recreate:
            client.delete(f"{uri}/collections/{collection}", headers=headers)
        exists_resp = client.get(f"{uri}/collections/{collection}", headers=headers)
        if exists_resp.status_code == 404:
            create_resp = client.put(
                f"{uri}/collections/{collection}",
                headers=headers,
                json={"vectors": {"size": dim, "distance": "Cosine"}},
            )
            create_resp.raise_for_status()
        else:
            exists_resp.raise_for_status()

        points = []
        for doc, vec in zip(docs, vectors):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"htmp-semantic:{doc['dataset_id']}"))
            text_hash = hashlib.sha256(doc["text"].encode("utf-8")).hexdigest()[:16]
            points.append({
                "id": point_id,
                "vector": vec,
                "payload": {
                    "dataset_id": doc["dataset_id"],
                    "title": doc["title"],
                    "version": doc["version"],
                    "text_hash": text_hash,
                },
            })
        upsert_resp = client.put(
            f"{uri}/collections/{collection}/points?wait=true",
            headers=headers,
            json={"points": points},
        )
        upsert_resp.raise_for_status()

    return {"collection": collection, "indexed_contracts": len(points), "vector_dim": dim}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qdrant-uri", default=None, help="Qdrant HTTP base URL (defaults to QDRANT_URI)")
    parser.add_argument("--collection", default=os.getenv("HTMP_SEMANTIC_QDRANT_COLLECTION", "htmp_erp_semantic_catalog"))
    parser.add_argument("--recreate", action="store_true", help="Drop and recreate the target Qdrant collection before upsert")
    args = parser.parse_args()
    summary = sync_qdrant_catalog(qdrant_uri=args.qdrant_uri, collection=args.collection, recreate=args.recreate)
    print(f"Indexed {summary['indexed_contracts']} contracts (dim={summary['vector_dim']}) into '{summary['collection']}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
