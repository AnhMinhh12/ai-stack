"""Hybrid BM25 + 3SERP metadata + multi-clause dataset retriever (no per-question hacks)."""
from __future__ import annotations

import math
import os
import re
import unicodedata
from collections import Counter
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


class HybridMetadataRetriever:
    """Zero-dependency BM25 + 3SERP UI metadata + field/cue retriever over semantic datasets."""

    def __init__(
        self,
        datasets: list[dict[str, Any]] | tuple[dict[str, Any], ...],
        *,
        contracts: dict[str, Any] | None = None,
        table_catalog: dict[str, dict[str, list[str]]] | None = None,
    ) -> None:
        self.datasets = [ds for ds in datasets if isinstance(ds, dict) and ds.get("id")]
        self._contracts = contracts or {}
        self._table_catalog = table_catalog if table_catalog is not None else build_3serp_table_catalog()
        self._docs_tf: list[Counter[str]] = []
        self._doc_lens: list[int] = []
        self._df: Counter[str] = Counter()
        self._avg_dl: float = 1.0
        self._meta_cache: list[dict[str, Any]] = []
        self._build_index()

    def _build_document_tokens(self, ds: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
        ds_id = str(ds["id"])
        contract = self._contracts.get(ds_id) if isinstance(self._contracts.get(ds_id), dict) else {}
        title = str(ds.get("title") or contract.get("title") or ds_id)
        notes = str(ds.get("notes") or contract.get("notes") or "")
        cues = [str(c) for c in (ds.get("cues") or contract.get("cues") or ()) if isinstance(c, str) and c]
        sec_cues = [str(c) for c in (ds.get("secondary_cues") or contract.get("secondary_cues") or ()) if isinstance(c, str) and c]

        enriched = enrich_contract_from_dictionary(contract, self._table_catalog) if contract else {"tables": [], "report_titles": [], "captions": []}

        # Build field text from declared field_labels + common semantic labels.
        field_labels = (ds.get("field_labels") or contract.get("field_labels") or {})
        field_parts: list[str] = []
        for fname in _dataset_field_names(ds):
            field_parts.append(fname.replace("_", " "))
            if isinstance(field_labels, dict) and fname in field_labels:
                field_parts.append(str(field_labels[fname]))
            if fname in _COMMON_FIELD_SYNONYMS:
                field_parts.append(_COMMON_FIELD_SYNONYMS[fname])

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
    ) -> list[tuple[float, dict[str, Any]]]:
        """Rank datasets using BM25 + 3SERP metadata + multi-clause boosting."""
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

        scored: list[tuple[float, dict[str, Any]]] = []
        for idx, ds in enumerate(self.datasets):
            bm25_q = self._bm25_score(idx, q_tokens)
            bm25_hist = 0.35 * self._bm25_score(idx, hist_tokens) if hist_tokens else 0.0
            cue_bonus = self._exact_cue_bonus(idx, q_norm, combined_norm)
            clause_bonus = clause_winners.get(idx, 0.0)
            total = bm25_q + bm25_hist + cue_bonus + clause_bonus
            # Suppress faint single-stopword noise when no strong cue/phrase matched.
            scored.append((round(total, 4), ds))

        scored.sort(key=lambda pair: (-pair[0], pair[1]["id"]))
        return scored


_INDEX_CACHE: dict[tuple[str, ...], HybridMetadataRetriever] = {}


def rank_datasets(
    question: str,
    history: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    datasets: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    *,
    contracts: dict[str, Any] | None = None,
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
        retriever = HybridMetadataRetriever(valid, contracts=contracts)
        _INDEX_CACHE[cache_key] = retriever
    return retriever.rank(question, history=history)


def optional_qdrant_dataset_hints(question: str) -> list[str]:
    """Optional Qdrant vector lookup when HTMP_SEMANTIC_QDRANT_COLLECTION is enabled."""
    collection = os.getenv("HTMP_SEMANTIC_QDRANT_COLLECTION", "").strip()
    qdrant_uri = os.getenv("QDRANT_URI", "").strip()
    embed_url = os.getenv("HTMP_SEMANTIC_EMBEDDING_URL", "").strip()
    if not (collection and qdrant_uri and embed_url):
        return []
    try:
        import httpx
        headers = {}
        api_key = os.getenv("QDRANT_API_KEY", "").strip()
        if api_key:
            headers["api-key"] = api_key
        with httpx.Client(timeout=2.0, trust_env=False) as client:
            emb_resp = client.post(embed_url, json={"input": question})
            emb_resp.raise_for_status()
            vector = emb_resp.json()["data"][0]["embedding"]
            search_resp = client.post(
                f"{qdrant_uri.rstrip('/')}/collections/{collection}/points/search",
                headers=headers,
                json={"vector": vector, "limit": 5, "with_payload": True},
            )
            search_resp.raise_for_status()
            return [
                str(pt.get("payload", {}).get("dataset_id"))
                for pt in search_resp.json().get("result", [])
                if isinstance(pt, dict) and pt.get("payload", {}).get("dataset_id")
            ]
    except Exception:
        return []
