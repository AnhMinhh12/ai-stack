"""Bounded conversation state for deterministic ERP filter inheritance."""

from collections import OrderedDict
from typing import Mapping
from threading import RLock
from .entities import extract_entities, merge_filters


class ConversationStateStore:
    """In-memory state; replace with Redis only when multi-replica is enabled."""

    def __init__(self, max_conversations: int = 2_000) -> None:
        self._max = max_conversations
        self._states: OrderedDict[str, dict[str, str]] = OrderedDict()
        self._lock = RLock()

    def resolve(self, conversation_id: str, question: str, context: str = "") -> dict[str, str]:
        """Merge explicit question values, provided context and prior state."""
        with self._lock:
            prior = dict(self._states.get(conversation_id, {})) if conversation_id else {}
            context_entities = extract_entities(context)
            question_entities = extract_entities(question)
            
            # Check if current question explicitly switches to a new topic or general entity
            import unicodedata, re
            norm_q = unicodedata.normalize("NFD", question or "").lower()
            norm_q = "".join(c for c in norm_q if unicodedata.category(c) != "Mn")
            norm_q = re.sub(r"[^a-z0-9]+", " ", norm_q.replace("đ", "d")).strip()
            
            new_topic_cues = (
                "model", "nha cung cap", "ncc", "khuon", "mold",
                "toan bo", "tat ca", "he thong", "danh sach", "danh muc",
                "nhua abs", "goc nhua",
                "file excel", "xuat excel", "bao nhieu ma"
            )
            has_new_topic = any(cue in norm_q for cue in new_topic_cues)
            if has_new_topic and not question_entities.get("ma_vt"):
                # Clear sticky material code so it doesn't contaminate unrelated queries
                prior.pop("ma_vt", None)
                context_entities.pop("ma_vt", None)

            # Tool-confirmed state is more reliable than model-generated
            # context, which can abbreviate codes (e.g. 35K-H2110-0001 to
            # H2110). The user's current explicit input still wins.
            merged = merge_filters(question_entities, merge_filters(prior, context_entities))
            if conversation_id:
                self._states[conversation_id] = {key: value for key, value in merged.items() if value}
                self._states.move_to_end(conversation_id)
                while len(self._states) > self._max:
                    self._states.popitem(last=False)
            return merged

    def remember(self, conversation_id: str, filters: Mapping[str, str]) -> None:
        """Persist filters resolved from a trusted ERP master-data lookup."""
        if not conversation_id:
            return
        with self._lock:
            prior = dict(self._states.get(conversation_id, {}))
            prior.update({key: value for key, value in filters.items() if value})
            self._states[conversation_id] = prior
            self._states.move_to_end(conversation_id)
            while len(self._states) > self._max:
                self._states.popitem(last=False)

    def clear(self, conversation_id: str) -> None:
        with self._lock:
            self._states.pop(conversation_id, None)
