"""Hybrid BM25 + 3SERP metadata + multi-clause dataset retriever (no per-question hacks)."""
from __future__ import annotations

import glob
import math
import os
import re
import threading
import time
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

from .semantic_catalog import build_3serp_table_catalog, enrich_contract_from_dictionary

_TOKEN_RE = re.compile(r"[a-z0-9_]+")
_CLAUSE_SPLIT_RE = re.compile(
    r"(?:\s+(?:va|kem|cung|so voi|dua theo|voi)\s+|[,;]+)",
    re.I,
)
_ACCENTED_STOPWORDS = frozenset({
    "mấy", "tôi", "cho", "em", "anh", "chị", "biết", "xem", "kiểm", "tra", "tìm", "lấy",
    "thống", "kê", "tổng", "hợp", "báo", "cáo", "danh", "sách", "liệt", "tin", "dữ", "liệu",
    "trong", "của", "các", "những", "nào", "gì", "bao", "nhiêu", "là", "hiện", "nay", "hành",
    "mới", "nhất", "gần", "đây", "tháng", "năm", "ngày", "từ", "đến", "theo", "từng", "top",
    "và", "với", "cùng", "để", "có", "được", "không", "cao", "thấp", "lớn", "nhỏ", "trung",
    "bình", "chính", "phụ", "loại", "dạng", "cần", "muốn", "sao", "tại", "vì", "tình", "hình",
    "mục", "chi", "tiết",
})

_QUERY_STOPWORDS = frozenset({
    "cho", "toi", "em", "anh", "chi", "biet", "xem", "kiem", "tra", "tim", "lay",
    "thong", "ke", "tong", "hop", "bao", "cao", "danh", "sach", "liet", "tin",
    "du", "lieu", "trong", "cua", "cac", "nhung", "nao", "gi", "nhieu", "la",
    "hien", "nay", "hanh", "moi", "nhat", "gan", "day", "thang", "nam", "ngay",
    "tu", "den", "theo", "tung", "top", "va", "voi", "cung", "de", "co", "duoc",
    "khong", "cao", "thap", "lon", "nho", "trung", "binh", "chinh", "phu", "loai",
    "dang", "can", "muon", "sao", "tai", "vi", "tinh", "hinh", "muc", "chi", "tiet",
})

# Lightweight canonical Vietnamese labels for common semantic field names so retrieval
# automatically indexes column semantics even without manual cues.
_COMMON_FIELD_SYNONYMS: dict[str, str] = {
    "customer": "ma khach hang customer",
    "customer_name": "ten khach hang",
    "supplier": "ma nha cung cap ncc",
    "supplier_name": "ten nha cung cap ncc",
    "material": "ma vat tu ma hang san pham",
    "material_name": "ten vat tu ten hang san pham",
    "product": "ma thanh pham san pham",
    "product_name": "ten thanh pham san pham",
    "warehouse": "ma kho",
    "warehouse_name": "ten kho",
    "machine": "ma may thiet bi",
    "line_group": "nhom may chuyen",
    "mold": "ma khuon",
    "mold_name": "ten khuon",
    "employee_code": "ma nhan vien",
    "employee_name": "ten nhan vien",
    "requester": "nguoi de nghi",
    "requester_name": "ten nguoi de nghi",
    "in_charge": "nguoi phu trach",
    "creator_user": "nguoi tao phieu user",
    "status_name": "trang thai",
    "doc_no": "so chung tu so phieu",
    "po_no": "so don hang mua po",
    "pr_no": "so phieu de nghi mua hang pr",
    "so_no": "so don hang ban so",
    "lot_no": "so lo",
    "work_order": "lenh san xuat wo",
    "quantity": "so luong",
    "revenue_vnd": "doanh thu thanh tien vnd",
    "amount_vnd": "thanh tien gia tri vnd",
    "amount_orig": "thanh tien nguyen te",
    "unit_price_vnd": "don gia gia mua gia ban",
    "unit_price_orig": "don gia nguyen te",
    "avg_price_vnd": "don gia don gia po",
    "moq": "moq so luong dat toi thieu",
    "oee_pct": "oee hieu suat thiet bi tong hop",
    "availability_pct": "kha dung availability",
    "performance_pct": "hieu suat performance",
    "quality_pct": "chat luong quality",
    "stop_minutes": "thoi gian dung may downtime phut",
    "stop_count": "so lan dung may",
    "reason_code": "ma nguyen nhan dung may",
    "reason_name": "nguyen nhan dung may ly do",
    "ng_qty": "so luong loi ng phe pham",
    "defect_code": "ma loi",
    "defect_name": "ten loi ng",
    "cavity": "so cavity long khuon",
    "cycle_sec": "chu ky ep giay",
    "total_shots": "tong so shot",
    "stock_qty": "so luong ton kho",
    "pending_qty": "so luong pending cho giao",
    "bom_qty": "dinh muc bom cau truc",
    "debit_vnd": "phat sinh no cong no",
    "credit_vnd": "phat sinh co cong no",
    "required_date": "ngay nhan hang yeu cau",
    "valid_from": "ngay hieu luc tu",
    "valid_to": "ngay hieu luc den",
    "expiry_date": "han su dung hsd",
}


def normalize_text(text: str) -> str:
    """Fold Vietnamese accents and lowercase whitespace consistently."""
    stripped = unicodedata.normalize("NFD", (text or "").replace("đ", "d").replace("Đ", "D"))
    cleaned = "".join(c for c in stripped if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", cleaned.lower()).strip()


def has_word_cue(text_norm: str, cue: str) -> bool:
    """Match cue with alphanumeric word boundaries to prevent substring collisions."""
    term = (cue or "").strip()
    if not term:
        return False
    return bool(re.search(rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])", text_norm))


def _tokenize(
    text: str,
    *,
    include_bigrams: bool = True,
    drop_stopwords: bool = False,
) -> list[str]:
    raw_norm = normalize_text(text)
    words_norm = [w for w in _TOKEN_RE.findall(raw_norm) if len(w) >= 2]
    if drop_stopwords:
        has_accents = any(ord(c) > 127 for c in (text or ""))
        if has_accents:
            raw_words = [w for w in re.findall(r"[^\W_]{2,}", (text or "").lower()) if w not in _ACCENTED_STOPWORDS]
            filtered = [w for w in (normalize_text(rw) for rw in raw_words) for w in _TOKEN_RE.findall(w) if len(w) >= 2]
        else:
            filtered = [w for w in words_norm if w not in _QUERY_STOPWORDS]
        if filtered:
            words_norm = filtered
    if not include_bigrams or len(words_norm) < 2:
        return words_norm
    bigrams = [f"{words_norm[i]}_{words_norm[i + 1]}" for i in range(len(words_norm) - 1)]
    return words_norm + bigrams


def _split_clauses(q_norm: str) -> list[str]:
    parts = [p.strip() for p in _CLAUSE_SPLIT_RE.split(q_norm or "") if p.strip()]
    clauses: list[str] = []
    for part in parts:
        toks = _tokenize(part, include_bigrams=False, drop_stopwords=True)
        if len(toks) >= 2:
            clauses.append(part)
    return clauses


def _dataset_field_names(ds: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for section in ("dimensions", "metrics", "filters"):
        raw = ds.get(section)
        if isinstance(raw, dict):
            out.extend(str(k) for k in raw)
        elif isinstance(raw, (list, tuple)):
            out.extend(str(k) for k in raw)
    return out


def _build_document_parts(
    ds: dict[str, Any],
    *,
    contract: dict[str, Any] | None = None,
    table_catalog: dict[str, dict[str, list[str]]] | None = None,
    field_catalog: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble shared semantic document fields/3SERP metadata once for both BM25 and dense vectors."""
    ds_id = str(ds["id"])
    c = contract if isinstance(contract, dict) else {}
    title = str(ds.get("title") or c.get("title") or ds_id)
    notes = str(ds.get("notes") or c.get("notes") or "")
    cues = [str(x) for x in (ds.get("cues") or c.get("cues") or ()) if isinstance(x, str) and x]
    sec_cues = [str(x) for x in (ds.get("secondary_cues") or c.get("secondary_cues") or ()) if isinstance(x, str) and x]
    cat = table_catalog if table_catalog is not None else build_3serp_table_catalog()
    enriched = enrich_contract_from_dictionary(c, cat) if c else {"tables": [], "report_titles": [], "captions": []}

    field_labels = ds.get("field_labels") or c.get("field_labels") or {}
    fcat = field_catalog if isinstance(field_catalog, dict) else {}
    field_parts: list[str] = []
    for fname in _dataset_field_names(ds):
        field_parts.append(fname.replace("_", " "))
        if isinstance(field_labels, dict) and fname in field_labels:
            field_parts.append(str(field_labels[fname]))
        elif fname in fcat and isinstance(fcat[fname], dict) and fcat[fname].get("label"):
            field_parts.append(str(fcat[fname]["label"]))
        if fname in _COMMON_FIELD_SYNONYMS:
            field_parts.append(_COMMON_FIELD_SYNONYMS[fname])

    return {
        "ds_id": ds_id,
        "title": title,
        "notes": notes,
        "cues": cues,
        "sec_cues": sec_cues,
        "enriched": enriched,
        "field_parts": field_parts,
    }


def document_text_for_dataset(
    ds: dict[str, Any],
    *,
    contract: dict[str, Any] | None = None,
    table_catalog: dict[str, dict[str, list[str]]] | None = None,
    field_catalog: dict[str, Any] | None = None,
) -> str:
    """Build canonical Vietnamese + technical text representation of a semantic dataset for BGE-M3 / Qdrant."""
    parts = _build_document_parts(
        ds,
        contract=contract,
        table_catalog=table_catalog,
        field_catalog=field_catalog,
    )
    enriched = parts["enriched"]
    lines = [
        f"Dataset: {parts['ds_id']} ({parts['ds_id'].replace('_', ' ')})",
        f"Tiêu đề: {parts['title']}",
    ]
    if enriched["report_titles"]:
        lines.append("Màn hình/Báo cáo 3SERP: " + "; ".join(enriched["report_titles"]))
    if parts["cues"]:
        lines.append("Từ khóa chính: " + ", ".join(parts["cues"]))
    if parts["sec_cues"]:
        lines.append("Từ khóa phụ: " + ", ".join(parts["sec_cues"]))
    if parts["field_parts"]:
        unique_fields = list(dict.fromkeys(parts["field_parts"]))
        lines.append("Trường dữ liệu & chỉ tiêu: " + ", ".join(unique_fields[:60]))
    if enriched["captions"]:
        lines.append("Cột lưới ERP/MES: " + ", ".join(enriched["captions"][:40]))
    if enriched["tables"]:
        lines.append("Bảng nguồn: " + ", ".join(enriched["tables"]))
    if parts["notes"]:
        lines.append("Ghi chú nghiệp vụ: " + parts["notes"])
    return "\n".join(lines)


def catalog_documents_for_indexing(
    config: dict[str, Any],
    *,
    table_catalog: dict[str, dict[str, list[str]]] | None = None,
) -> list[dict[str, str]]:
    """Return approved semantic contract documents formatted for Qdrant vector indexing."""
    contracts = config.get("semantic_contracts") or {}
    field_catalog = config.get("field_catalog") if isinstance(config.get("field_catalog"), dict) else {}
    cat = table_catalog if table_catalog is not None else build_3serp_table_catalog()
    docs: list[dict[str, str]] = []
    for ds_id in sorted(contracts):
        contract = contracts.get(ds_id)
        if not isinstance(contract, dict) or contract.get("status") != "approved":
            continue
        ds = {
            "id": ds_id,
            "title": contract.get("title") or ds_id,
            "dimensions": sorted(contract.get("dimensions") or ()),
            "metrics": sorted(contract.get("metrics") or ()),
            "filters": sorted(contract.get("filters") or ()),
            "cues": contract.get("cues") or (),
            "secondary_cues": contract.get("secondary_cues") or (),
            "field_labels": contract.get("field_labels") or {},
            "notes": contract.get("notes") or "",
        }
        docs.append({
            "dataset_id": ds_id,
            "title": str(ds["title"]),
            "version": str(contract.get("version") or ""),
            "text": document_text_for_dataset(
                ds,
                contract=contract,
                table_catalog=cat,
                field_catalog=field_catalog,
            ),
        })
    return docs


def fuse_rrf_scores(
    bm25_ranked_ids: list[str] | tuple[str, ...],
    vector_ranked_ids: list[str] | tuple[str, ...],
    *,
    k: int = 60,
    bm25_weight: float = 1.0,
    vector_weight: float = 1.0,
) -> dict[str, float]:
    """Compute Reciprocal Rank Fusion (RRF) scores across lexical BM25 and dense vector rankings."""
    scores: dict[str, float] = {}
    if bm25_weight:
        for rank_idx, ds_id in enumerate(bm25_ranked_ids, start=1):
            if ds_id:
                scores[ds_id] = scores.get(ds_id, 0.0) + bm25_weight / float(k + rank_idx)
    if vector_weight:
        for rank_idx, ds_id in enumerate(vector_ranked_ids, start=1):
            if ds_id:
                scores[ds_id] = scores.get(ds_id, 0.0) + vector_weight / float(k + rank_idx)
    return scores


class HybridMetadataRetriever:
    """BM25 + 3SERP metadata + optional BGE-M3/Qdrant RRF hybrid retriever over semantic datasets."""

    def __init__(
        self,
        datasets: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        *,
        contracts: dict[str, Any] | None = None,
        table_catalog: dict[str, dict[str, list[str]]] | None = None,
        field_catalog: dict[str, Any] | None = None,
    ) -> None:
        self.datasets = [ds for ds in datasets if isinstance(ds, dict) and ds.get("id")]
        self._contracts = contracts or {}
        self._table_catalog = table_catalog if table_catalog is not None else build_3serp_table_catalog()
        self._field_catalog = field_catalog or {}
        self._docs_tf: list[Counter[str]] = []
        self._doc_lens: list[int] = []
        self._df: Counter[str] = Counter()
        self._avg_dl: float = 1.0
        self._meta_cache: list[dict[str, Any]] = []
        self._build_index()

    def _build_document_tokens(self, ds: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
        parts = _build_document_parts(
            ds,
            contract=self._contracts.get(str(ds["id"])),
            table_catalog=self._table_catalog,
            field_catalog=self._field_catalog,
        )
        ds_id = parts["ds_id"]
        title = parts["title"]
        notes = parts["notes"]
        cues = parts["cues"]
        sec_cues = parts["sec_cues"]
        enriched = parts["enriched"]
        field_parts = parts["field_parts"]

        # Weighted token bag (deduplicated per section so length normalization works cleanly):
        # title + 3SERP report titles (2x), cues + captions + fields (1-2x), notes + tables (1x).
        tokens: list[str] = []
        high_text = normalize_text(" ".join([ds_id.replace("_", " "), title, *enriched["report_titles"]]))
        cue_text = normalize_text(" ".join(cues))
        mid_text = normalize_text(" ".join([*field_parts, *enriched["captions"]]))
        sec_text = normalize_text(" ".join([*sec_cues, notes, *enriched["tables"]]))

        high_toks = list(dict.fromkeys(_tokenize(high_text, include_bigrams=True, drop_stopwords=True)))
        cue_toks = list(dict.fromkeys(_tokenize(cue_text, include_bigrams=True, drop_stopwords=False)))
        mid_toks = list(dict.fromkeys(_tokenize(mid_text, include_bigrams=True, drop_stopwords=True)))
        sec_toks = list(dict.fromkeys(_tokenize(sec_text, include_bigrams=True, drop_stopwords=True)))
        tokens.extend(high_toks * 2)
        tokens.extend(cue_toks * 2)
        tokens.extend(mid_toks)
        tokens.extend(sec_toks)

        meta = {
            "primary_cues": [normalize_text(c) for c in cues],
            "secondary_cues": [normalize_text(c) for c in sec_cues],
            "title_norm": normalize_text(title),
        }
        return tokens, meta

    def _build_index(self) -> None:
        self._docs_tf = []
        self._doc_lens = []
        self._df = Counter()
        self._meta_cache = []
        for ds in self.datasets:
            toks, meta = self._build_document_tokens(ds)
            tf = Counter(toks)
            self._docs_tf.append(tf)
            self._doc_lens.append(len(toks) or 1)
            for term in tf:
                self._df[term] += 1
            self._meta_cache.append(meta)
        n_docs = len(self.datasets)
        self._avg_dl = (sum(self._doc_lens) / n_docs) if n_docs else 1.0

    def _bm25_score(self, doc_idx: int, q_tokens: list[str], *, k1: float = 1.5, b: float = 0.65) -> float:
        n_docs = len(self.datasets)
        if not n_docs or not q_tokens:
            return 0.0
        tf = self._docs_tf[doc_idx]
        dl = self._doc_lens[doc_idx]
        score = 0.0
        for term in set(q_tokens):
            f = tf.get(term, 0)
            if f <= 0:
                continue
            df = self._df.get(term, 0)
            idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
            denom = f + k1 * (1.0 - b + b * (dl / self._avg_dl))
            weight = 1.6 if "_" in term else 1.0
            score += weight * idf * (f * (k1 + 1.0) / denom)
        return score

    def _exact_cue_bonus(self, doc_idx: int, q_norm: str, combined_norm: str) -> float:
        meta = self._meta_cache[doc_idx]
        bonus = 0.0
        for cue in meta["primary_cues"]:
            matched_q = has_word_cue(q_norm, cue) if len(cue) <= 4 else (has_word_cue(q_norm, cue) or (" " in cue and cue in q_norm))
            matched_ctx = has_word_cue(combined_norm, cue) if len(cue) <= 4 else (has_word_cue(combined_norm, cue) or (" " in cue and cue in combined_norm))
            if matched_q:
                bonus += 3.0 + (1.5 if " " in cue else 0.0)
            elif matched_ctx:
                bonus += 1.5
        for cue in meta["secondary_cues"]:
            matched_q = has_word_cue(q_norm, cue) if len(cue) <= 4 else (has_word_cue(q_norm, cue) or (" " in cue and cue in q_norm))
            if matched_q:
                bonus += 1.2
        return bonus

    def rank(
        self,
        question: str,
        history: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
        *,
        vector_hits: list[str] | tuple[str, ...] | None = None,
    ) -> list[tuple[float, dict[str, Any]]]:
        """Rank datasets using BM25 + 3SERP metadata + multi-clause boosting + optional BGE-M3 Qdrant RRF."""
        user_history = [
            str(m.get("content") or "")
            for m in history
            if isinstance(m, dict) and m.get("role") == "user" and isinstance(m.get("content"), str)
        ][-3:]
        q_norm = normalize_text(question)
        combined_norm = normalize_text(" ".join([*user_history, question]))

        q_tokens = _tokenize(question, include_bigrams=True, drop_stopwords=True)
        hist_tokens = _tokenize(" ".join(user_history), include_bigrams=True, drop_stopwords=True)
        clauses = _split_clauses(q_norm)
        clause_tokens_list = [_tokenize(c, include_bigrams=True, drop_stopwords=True) for c in clauses]

        # If the question has >= 2 meaningful clauses, keep the strongest candidate per clause
        # so multi-part questions always surface datasets for ALL parts.
        clause_winners: dict[int, float] = {}
        if len(clause_tokens_list) >= 2:
            for c_toks in clause_tokens_list:
                best_idx = -1
                best_score = 0.0
                for idx in range(len(self.datasets)):
                    s = self._bm25_score(idx, c_toks)
                    if s > best_score:
                        best_score = s
                        best_idx = idx
                if best_idx >= 0 and best_score > 0.5:
                    clause_winners[best_idx] = max(clause_winners.get(best_idx, 0.0), best_score * 0.65)

        raw_scores: list[tuple[int, float]] = []
        for idx in range(len(self.datasets)):
            bm25_q = self._bm25_score(idx, q_tokens)
            bm25_hist = 0.35 * self._bm25_score(idx, hist_tokens) if hist_tokens else 0.0
            cue_bonus = self._exact_cue_bonus(idx, q_norm, combined_norm)
            clause_bonus = clause_winners.get(idx, 0.0)
            raw_scores.append((idx, bm25_q + bm25_hist + cue_bonus + clause_bonus))

        vec_ids = (
            [str(v) for v in vector_hits if v]
            if vector_hits is not None
            else optional_qdrant_dataset_hints(question, limit=12)
        )
        rrf_vec: dict[str, float] = {}
        if vec_ids:
            allowed_ids = {str(ds["id"]) for ds in self.datasets}
            filtered_vec_ids = [vid for vid in vec_ids if vid in allowed_ids]
            if filtered_vec_ids:
                rrf_vec = fuse_rrf_scores([], filtered_vec_ids, k=60, bm25_weight=0.0, vector_weight=1.0)

        scored: list[tuple[float, dict[str, Any]]] = []
        for idx, base_total in raw_scores:
            ds = self.datasets[idx]
            vec_boost = 450.0 * rrf_vec.get(str(ds["id"]), 0.0) if rrf_vec else 0.0
            scored.append((round(base_total + vec_boost, 4), ds))

        scored.sort(key=lambda pair: (-pair[0], pair[1]["id"]))
        return scored


_INDEX_CACHE: dict[tuple[str, ...], HybridMetadataRetriever] = {}
_EMBEDDER_LOCK = threading.Lock()
_EMBEDDER_INSTANCE: Any = None
_EMBEDDER_FAILED_AT: float = 0.0
_QDRANT_UNAVAILABLE_UNTIL: float = 0.0


def resolve_local_embedding_model_path() -> str | None:
    """Locate cached local BGE-M3 / RAG embedding snapshot without network downloads."""
    explicit = os.getenv("HTMP_SEMANTIC_EMBEDDING_MODEL_PATH", "").strip()
    if explicit and Path(explicit).exists():
        return explicit
    model_name = os.getenv("RAG_EMBEDDING_MODEL", "BAAI/bge-m3").strip() or "BAAI/bge-m3"
    repo_dir = f"models--{model_name.replace('/', '--')}"
    roots = [
        "/app/backend/data/cache/embedding/models",
        os.path.expanduser("~/.cache/huggingface/hub"),
    ]
    for root in roots:
        snaps = sorted(glob.glob(f"{root}/{repo_dir}/snapshots/*"))
        if snaps:
            return snaps[-1]
    return None


def _get_local_embedder() -> Any:
    """Lazily initialize CPU SentenceTransformer once from local cache only."""
    global _EMBEDDER_INSTANCE, _EMBEDDER_FAILED_AT
    if _EMBEDDER_INSTANCE is not None:
        return _EMBEDDER_INSTANCE
    if time.monotonic() - _EMBEDDER_FAILED_AT < 60.0:
        return None
    with _EMBEDDER_LOCK:
        if _EMBEDDER_INSTANCE is not None:
            return _EMBEDDER_INSTANCE
        model_path = resolve_local_embedding_model_path()
        if not model_path:
            _EMBEDDER_FAILED_AT = time.monotonic()
            return None
        try:
            from sentence_transformers import SentenceTransformer

            _EMBEDDER_INSTANCE = SentenceTransformer(
                model_path,
                device="cpu",
                local_files_only=True,
            )
            return _EMBEDDER_INSTANCE
        except Exception:
            _EMBEDDER_FAILED_AT = time.monotonic()
            return None


def encode_texts_bge_m3(texts: list[str] | tuple[str, ...]) -> list[list[float]]:
    """Encode texts locally with cached BAAI/bge-m3 when available; return [] on error."""
    if not texts:
        return []
    embedder = _get_local_embedder()
    if embedder is None:
        return []
    try:
        vecs = embedder.encode(list(texts), normalize_embeddings=True, show_progress_bar=False)
        return [vec.tolist() if hasattr(vec, "tolist") else [float(x) for x in vec] for vec in vecs]
    except Exception:
        return []


def rank_datasets(
    question: str,
    history: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    datasets: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    *,
    contracts: dict[str, Any] | None = None,
    field_catalog: dict[str, Any] | None = None,
    vector_hits: list[str] | tuple[str, ...] | None = None,
) -> list[tuple[float, dict[str, Any]]]:
    """Cached entry point for hybrid ranking of semantic datasets."""
    valid = [ds for ds in datasets if isinstance(ds, dict) and ds.get("id")]
    if not valid:
        return []
    cache_key = tuple(
        f"{ds['id']}:{ds.get('version', '')}:{len(ds.get('cues') or ())}:{len(ds.get('dimensions') or ())}"
        for ds in valid
    ) + (("has_contracts" if contracts else "no_contracts"),)
    retriever = _INDEX_CACHE.get(cache_key)
    if retriever is None:
        if len(_INDEX_CACHE) > 16:
            _INDEX_CACHE.clear()
        retriever = HybridMetadataRetriever(valid, contracts=contracts, field_catalog=field_catalog)
        _INDEX_CACHE[cache_key] = retriever
    return retriever.rank(question, history=history, vector_hits=vector_hits)


def optional_qdrant_dataset_hints(question: str, *, limit: int = 10) -> list[str]:
    """Fail-open dense BGE-M3 + Qdrant vector lookup when QDRANT_URI and collection exist."""
    global _QDRANT_UNAVAILABLE_UNTIL
    if os.getenv("HTMP_SEMANTIC_VECTOR_ENABLED", "1").strip().lower() in ("0", "false", "off", "disabled"):
        return []
    qdrant_uri = os.getenv("QDRANT_URI", "").strip()
    collection = os.getenv("HTMP_SEMANTIC_QDRANT_COLLECTION", "htmp_erp_semantic_catalog").strip()
    if not (collection and qdrant_uri) or not (question or "").strip():
        return []
    if time.monotonic() < _QDRANT_UNAVAILABLE_UNTIL:
        return []
    try:
        import httpx

        headers = {}
        api_key = os.getenv("QDRANT_API_KEY", "").strip()
        if api_key:
            headers["api-key"] = api_key
        embed_url = os.getenv("HTMP_SEMANTIC_EMBEDDING_URL", "").strip()
        min_score = float(os.getenv("HTMP_SEMANTIC_VECTOR_MIN_SCORE", "0.38"))
        vector: list[float] | None = None
        with httpx.Client(timeout=2.0, trust_env=False) as client:
            if embed_url:
                emb_resp = client.post(embed_url, json={"input": question})
                emb_resp.raise_for_status()
                vector = emb_resp.json()["data"][0]["embedding"]
            else:
                vecs = encode_texts_bge_m3([question])
                vector = vecs[0] if vecs else None
            if not vector:
                return []
            search_resp = client.post(
                f"{qdrant_uri.rstrip('/')}/collections/{collection}/points/search",
                headers=headers,
                json={"vector": vector, "limit": limit, "score_threshold": min_score, "with_payload": True},
            )
            if search_resp.status_code == 404:
                _QDRANT_UNAVAILABLE_UNTIL = time.monotonic() + 60.0
                return []
            search_resp.raise_for_status()
            return [
                str(pt.get("payload", {}).get("dataset_id"))
                for pt in search_resp.json().get("result", [])
                if isinstance(pt, dict) and pt.get("payload", {}).get("dataset_id")
            ]
    except Exception:
        _QDRANT_UNAVAILABLE_UNTIL = time.monotonic() + 60.0
        return []
