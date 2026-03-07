"""Broadcast tool for bulk messaging."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from fastmcp import FastMCP

from ..context import BotContext
from .messaging import _normalize_parse_mode

logger = logging.getLogger(__name__)
ToolResult = dict[str, Any]


def register_broadcast_tools(
    mcp: FastMCP,
    ctx: BotContext,
    max_recipients: int = 100,
) -> None:
    @mcp.tool
    async def broadcast(
        chat_ids: list[int],
        text: str,
        parse_mode: str | None = "HTML",
        delay_seconds: float = 0.05,
        dry_run: bool = True,
    ) -> ToolResult:
        """Send a message to multiple users or chats."""
        if len(chat_ids) > max_recipients:
            return {
                "ok": False,
                "error": (
                    f"Recipient count {len(chat_ids)} exceeds safety limit "
                    f"of {max_recipients}. Adjust max_broadcast_recipients in "
                    "AiogramMCP to increase this limit."
                ),
            }

        if ctx.allowed_chat_ids is not None:
            blocked = [chat_id for chat_id in chat_ids if not ctx.is_chat_allowed(chat_id)]
            if blocked:
                return {
                    "ok": False,
                    "error": f"These chat IDs are not in allowed_chat_ids: {blocked}",
                }

        if dry_run:
            return {
                "ok": True,
                "dry_run": True,
                "would_send_to": len(chat_ids),
                "recipients": chat_ids,
                "message_preview": text[:200],
                "note": "Set dry_run=False to actually send.",
            }

        try:
            normalized_parse_mode = _normalize_parse_mode(parse_mode)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}

        results: list[ToolResult] = []
        success = 0
        failed = 0

        for chat_id in chat_ids:
            try:
                await ctx.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=normalized_parse_mode,
                )
                results.append({"chat_id": chat_id, "ok": True})
                success += 1
            except TelegramForbiddenError:
                results.append({"chat_id": chat_id, "ok": False, "error": "blocked"})
                failed += 1
            except TelegramBadRequest as exc:
                results.append({"chat_id": chat_id, "ok": False, "error": str(exc)})
                failed += 1

            await asyncio.sleep(delay_seconds)

        logger.info("Broadcast complete: %d success, %d failed", success, failed)

        return {
            "ok": True,
            "dry_run": False,
            "success_count": success,
            "failed_count": failed,
            "results": results,
        }
