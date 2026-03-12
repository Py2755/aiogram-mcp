"""Shared utilities for aiogram-mcp."""

from __future__ import annotations

from aiogram.enums import ParseMode


def normalize_parse_mode(parse_mode: str | None) -> ParseMode | None:
    """Convert a string parse_mode to aiogram ParseMode enum.

    Accepts: HTML, Markdown, MarkdownV2 (case-insensitive), or None.
    """
    if parse_mode is None:
        return None
    normalized = parse_mode.strip().upper()
    if normalized == "HTML":
        return ParseMode.HTML
    if normalized in {"MARKDOWN", "MARKDOWNV2"}:
        return ParseMode.MARKDOWN_V2
    raise ValueError("parse_mode must be one of: HTML, Markdown, MarkdownV2, or None")
