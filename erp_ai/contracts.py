"""Stable contracts between natural-language parsing and ERP execution."""

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ERPRequest:
    intent: str
    filters: dict[str, str] = field(default_factory=dict)
    metrics: tuple[str, ...] = ()
    dimensions: tuple[str, ...] = ()
    source: str = "current_turn"


@dataclass
class ERPResult:
    status: str
    intent: str
    filters: dict[str, str]
    summary: dict[str, Any] = field(default_factory=dict)
    rows: list[dict[str, Any]] = field(default_factory=list)
    total_rows: int = 0
    returned_rows: int = 0
    has_more: bool = False
    error_code: str | None = None
    message: str | None = None

    def payload(self) -> dict[str, Any]:
        data = asdict(self)
        data["query"] = {"intent": self.intent, "filters": self.filters}
        data.pop("intent")
        data.pop("filters")
        return data
