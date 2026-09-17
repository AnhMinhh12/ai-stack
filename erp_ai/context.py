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
            merged = merge_filters(question_entities, merge_filters(context_entities, prior))
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
