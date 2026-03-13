"""Audit logging for MCP tool invocations."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel


class AuditEntry(BaseModel):
    """A single audit log entry for a tool invocation."""

    id: int
    timestamp: datetime
    tool: str
    args: dict[str, Any]
    ok: bool
    error: str | None = None


class AuditLogger:
    """In-memory audit log with fixed capacity."""

    def __init__(self, max_size: int = 500) -> None:
        self._max_size = max_size
        self._next_id: int = 1
        self._entries: deque[AuditEntry] = deque(maxlen=max_size)

    def log(
        self, tool: str, args: dict[str, Any], ok: bool, error: str | None = None
    ) -> None:
        """Record a tool invocation."""
        entry = AuditEntry(
            id=self._next_id,
            timestamp=datetime.now(timezone.utc),
            tool=tool,
            args=args,
            ok=ok,
            error=error,
        )
        self._next_id += 1
        self._entries.append(entry)

    def get_entries(self, since_id: int = 0) -> list[AuditEntry]:
        """Return entries with id > since_id."""
        return [e for e in self._entries if e.id > since_id]
