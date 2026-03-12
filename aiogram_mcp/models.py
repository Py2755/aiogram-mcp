"""Base Pydantic models for MCP tool responses."""

from __future__ import annotations

from pydantic import BaseModel


class ToolResponse(BaseModel):
    """Base model for all tool results. ok=True on success, ok=False with error on failure."""

    ok: bool
    error: str | None = None


class OkResult(ToolResponse):
    """Result for tools that return only ok/error (delete, pin, etc.)."""

    pass
