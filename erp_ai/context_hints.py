"""Deterministic date, entity, and dataset hints extracted without DB I/O."""
from __future__ import annotations

import calendar
import re
import unicodedata
from datetime import date
from typing import Any

from .entities import extract_entities, merge_filters

_DMY_DATE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
_ISO_DATE = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")
_MONTH = re.compile(r"\b(?:tháng|thang)\s*(\d{1,2})\s*(?:/|[-.]|\s+(?:năm|nam)\s+|\s+)(\d{4})\b", re.I)

_DEFAULT_PERSON_CUES = (
    "nhan vien", "nguoi tao", "nguoi lap", "nguoi de nghi", "phu trach",
    "viet phieu", "dat mua", "ai", "cua ai", "user", "username",
)


def _has_cue(text: str, cue: str) -> bool:
    term = (cue or "").strip()
    if not term:
        return False
    return bool(re.search(rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])", text))


def _norm(text: str) -> str:
    stripped = unicodedata.normalize("NFD", (text or "").replace("đ", "d").replace("Đ", "D"))
    cleaned = "".join(c for c in stripped if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", cleaned.lower()).strip()


def _extract_dates_from_text(text: str) -> tuple[list[str], list[dict[str, str]]]:
    iso_dates: list[str] = []
    for y, m, d in _ISO_DATE.findall(text or ""):
        try:
            iso = date(int(y), int(m), int(d)).isoformat()
            if iso not in iso_dates:
                iso_dates.append(iso)
        except ValueError:
            pass
    for d, m, y in _DMY_DATE.findall(text or ""):
        try:
            iso = date(int(y), int(m), int(d)).isoformat()
            if iso not in iso_dates:
                iso_dates.append(iso)
        except ValueError:
            pass
    months: list[dict[str, str]] = []
    seen_months = set()
    for m_str, y_str in _MONTH.findall(text or ""):
        month, year = int(m_str), int(y_str)
        if 1 <= month <= 12 and 1 <= year <= 9999:
            key = f"{month:02d}/{year:04d}"
            if key not in seen_months:
                seen_months.add(key)
                last_day = calendar.monthrange(year, month)[1]
                months.append({
                    "label": key,
                    "start": f"{year:04d}-{month:02d}-01",
                    "end": f"{year:04d}-{month:02d}-{last_day:02d}",
                })
    return iso_dates, months


def _score_dataset(ds: dict[str, Any], q_norm: str, combined_norm: str) -> int:
    primary_cues = [c for c in (ds.get("cues") or ()) if isinstance(c, str) and c]
    secondary_cues = [c for c in (ds.get("secondary_cues") or ()) if isinstance(c, str) and c]
    score = 0
    for cue in primary_cues:
        matched_q = _has_cue(q_norm, cue) if len(cue) <= 4 else (cue in q_norm)
        matched_ctx = _has_cue(combined_norm, cue) if len(cue) <= 4 else (cue in combined_norm)
        word_bonus = 2 if " " in cue else 0
        if matched_q:
            score += 4 + word_bonus
        if matched_ctx:
            score += 2
    for cue in secondary_cues:
        matched_q = _has_cue(q_norm, cue) if len(cue) <= 4 else (cue in q_norm)
        matched_ctx = _has_cue(combined_norm, cue) if len(cue) <= 4 else (cue in combined_norm)
        if matched_q:
            score += 3
        if matched_ctx:
            score += 1
    return score


def score_datasets(
    question: str,
    history: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    datasets: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
) -> list[tuple[int, dict[str, Any]]]:
    """Score and rank datasets against question + recent user history."""
    user_history = [
        str(m.get("content") or "")
        for m in history
        if isinstance(m, dict) and m.get("role") == "user" and isinstance(m.get("content"), str)
    ][-3:]
    q_norm = _norm(question)
    combined_norm = _norm(" ".join([*user_history, question]))
    scored = []
    for ds in datasets:
        if isinstance(ds, dict) and ds.get("id"):
            s = _score_dataset(ds, q_norm, combined_norm)
            scored.append((s, ds))
    scored.sort(key=lambda pair: (-pair[0], pair[1]["id"]))
    return scored


def extract_context_hints(
    question: str,
    history: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    datasets: list[dict[str, Any]] | tuple[dict[str, Any], ...] = (),
    person_cues: list[str] | tuple[str, ...] | None = None,
    person_lookup_tool: str = "",
) -> dict[str, Any]:
    """Build deterministic date, entity, and dataset routing hints from metadata."""
    user_history = [
        str(m.get("content") or "")
        for m in history
        if isinstance(m, dict) and m.get("role") == "user" and isinstance(m.get("content"), str)
    ][-3:]

    q_dates, q_months = _extract_dates_from_text(question)
    dates_from_history = False
    if not q_dates and not q_months:
        for prev in reversed(user_history):
            p_dates, p_months = _extract_dates_from_text(prev)
            if p_dates or p_months:
                q_dates, q_months = p_dates, p_months
                dates_from_history = True
                break

    merged_entities = extract_entities(question)
    for prev in reversed(user_history):
        merged_entities = merge_filters(merged_entities, extract_entities(prev))
    merged_entities = {k: v for k, v in merged_entities.items() if v}

    combined_norm = _norm(" ".join([*user_history, question]))
    ranked = [ds for score, ds in score_datasets(question, history, datasets) if score > 0]
    recommended = ranked[:5]

    active_person_cues = tuple(person_cues) if person_cues else _DEFAULT_PERSON_CUES
    hints: dict[str, Any] = {"today": date.today().isoformat()}
    if q_dates:
        hints["detected_dates_iso"] = q_dates
    if q_months:
        hints["detected_months"] = q_months
    if dates_from_history:
        hints["dates_inherited_from_history"] = True
    if merged_entities:
        hints["detected_entities"] = merged_entities
    if any(_has_cue(combined_norm, cue) for cue in active_person_cues):
        hints["employee_lookup_suggested"] = True
        if person_lookup_tool:
            hints["suggested_lookup_tool"] = person_lookup_tool
    if recommended:
        hints["recommended_datasets"] = []
        for ds in recommended:
            item = {
                "id": ds["id"],
                "dimensions": ds.get("dimensions", []),
                "metrics": ds.get("metrics", []),
                "filters": ds.get("filters", []),
                "require_bounded_date": ds.get("require_bounded_date", True),
            }
            if ds.get("notes"):
                item["notes"] = ds["notes"]
            recommended_target = hints["recommended_datasets"]
            recommended_target.append(item)
    return hints
