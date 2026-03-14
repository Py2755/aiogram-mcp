"""Broadcast tool for bulk messaging."""

from __future__ import annotations

import asyncio
import logging

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from fastmcp import FastMCP
from pydantic import BaseModel

from ..context import BotContext
from ..models import ToolResponse
from ..utils import normalize_parse_mode

logger = logging.getLogger(__name__)


class BroadcastRecipientResult(BaseModel):
    chat_id: int
    ok: bool
    error: str | None = None


class BroadcastResult(ToolResponse):
    dry_run: bool | None = None
    would_send_to: int | None = None
    recipients: list[int] | None = None
    message_preview: str | None = None
    note: str | None = None
    success_count: int | None = None
    failed_count: int | None = None
    results: list[BroadcastRecipientResult] | None = None


def register_broadcast_tools(
    mcp: FastMCP,
    ctx: BotContext,
    max_recipients: int = 100,
    allowed_tools: set[str] | None = None,
) -> None:
    if allowed_tools is None or "broadcast" in allowed_tools:

        @mcp.tool
        async def broadcast(
            chat_ids: list[int],
            text: str,
            parse_mode: str | None = "HTML",
            delay_seconds: float = 0.05,
            dry_run: bool = True,
        ) -> BroadcastResult:
            """Send a message to multiple users or chats."""
            audit_args = {"chat_ids": chat_ids, "dry_run": dry_run}

            if len(chat_ids) > max_recipients:
                result = BroadcastResult(
                    ok=False,
                    error=(
                        f"Recipient count {len(chat_ids)} exceeds safety limit "
                        f"of {max_recipients}. Adjust max_broadcast_recipients in "
                        "AiogramMCP to increase this limit."
                    ),
                )
                if ctx.audit_logger:
                    ctx.audit_logger.log("broadcast", audit_args, result.ok, result.error)
                return result

            if ctx.allowed_chat_ids is not None:
                blocked = [chat_id for chat_id in chat_ids if not ctx.is_chat_allowed(chat_id)]
                if blocked:
                    result = BroadcastResult(
                        ok=False,
                        error=f"These chat IDs are not in allowed_chat_ids: {blocked}",
                    )
                    if ctx.audit_logger:
                        ctx.audit_logger.log("broadcast", audit_args, result.ok, result.error)
                    return result

            if dry_run:
                result = BroadcastResult(
                    ok=True,
                    dry_run=True,
                    would_send_to=len(chat_ids),
                    recipients=chat_ids,
                    message_preview=text[:200],
                    note="Set dry_run=False to actually send.",
                )
                if ctx.audit_logger:
                    ctx.audit_logger.log("broadcast", audit_args, result.ok, result.error)
                return result

            try:
                normalized_parse_mode = normalize_parse_mode(parse_mode)
            except ValueError as exc:
                result = BroadcastResult(ok=False, error=str(exc))
                if ctx.audit_logger:
                    ctx.audit_logger.log("broadcast", audit_args, result.ok, result.error)
                return result

            results: list[BroadcastRecipientResult] = []
            success = 0
            failed = 0

            for chat_id in chat_ids:
                try:
                    if ctx.rate_limiter:
                        await ctx.rate_limiter.acquire()
                    await ctx.bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        parse_mode=normalized_parse_mode,
                    )
                    results.append(BroadcastRecipientResult(chat_id=chat_id, ok=True))
                    success += 1
                except TelegramForbiddenError:
                    results.append(
                        BroadcastRecipientResult(chat_id=chat_id, ok=False, error="blocked")
                    )
                    failed += 1
                except TelegramBadRequest as exc:
                    results.append(
                        BroadcastRecipientResult(chat_id=chat_id, ok=False, error=str(exc))
                    )
                    failed += 1

                if not ctx.rate_limiter:
                    await asyncio.sleep(delay_seconds)

            logger.info("Broadcast complete: %d success, %d failed", success, failed)

            result = BroadcastResult(
                ok=True,
                dry_run=False,
                success_count=success,
                failed_count=failed,
                results=results,
            )
            if ctx.audit_logger:
                ctx.audit_logger.log("broadcast", audit_args, result.ok, result.error)
            return result
