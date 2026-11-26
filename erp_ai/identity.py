"""ERP identity mappings supplied by the server."""

import json
import os
from typing import Any


def mapped_erp_user_id(user: Any) -> int | None:
    """Resolve a WebUI user through the server map without a shared account."""
    if not isinstance(user, dict):
        return None
    try:
        mapping = json.loads(os.getenv("HTMP_ERP_USER_ID_MAP", "{}"))
    except ValueError:
        return None
    if not isinstance(mapping, dict):
        return None

    for identity in (str(user.get("id") or ""), str(user.get("email") or "").lower()):
        if not identity:
            continue
        value = mapping.get(identity)
        if type(value) is int and value > 0:
            return value
        if isinstance(value, str) and value.isdecimal():
            try:
                parsed = int(value)
            except ValueError:
                continue
            if parsed > 0:
                return parsed
    return None
