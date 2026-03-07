"""Messaging tools: send_message, send_photo, forward_message, delete_message, pin_message."""

from __future__ import annotations

from typing import Any

from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import ReplyParameters
from fastmcp import FastMCP

from ..context import BotContext

ToolResult = dict[str, Any]


def _normalize_parse_mode(parse_mode: str | None) -> ParseMode | None:
    if parse_mode is None:
        return None
    normalized = parse_mode.strip().upper()
    if normalized == "HTML":
        return ParseMode.HTML
    if normalized in {"MARKDOWN", "MARKDOWNV2"}:
        return ParseMode.MARKDOWN_V2
    raise ValueError("parse_mode must be one of: HTML, Markdown, MarkdownV2, or None")


def register_messaging_tools(mcp: FastMCP, ctx: BotContext) -> None:
    @mcp.tool
    async def send_message(
        chat_id: int,
        text: str,
        parse_mode: str | None = "HTML",
        disable_notification: bool = False,
        reply_to_message_id: int | None = None,
    ) -> ToolResult:
        """Send a text message to a Telegram chat or user."""
        if not ctx.is_chat_allowed(chat_id):
            return {
                "ok": False,
                "error": f"Chat {chat_id} is not in the allowed_chat_ids whitelist.",
            }

        try:
            msg = await ctx.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=_normalize_parse_mode(parse_mode),
                disable_notification=disable_notification,
                reply_parameters=(
                    ReplyParameters(message_id=reply_to_message_id)
                    if reply_to_message_id is not None
                    else None
                ),
            )
            return {
                "ok": True,
                "message_id": msg.message_id,
                "chat_id": msg.chat.id,
                "date": msg.date.isoformat(),
            }
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        except TelegramForbiddenError:
            return {"ok": False, "error": "Bot was blocked by the user or lacks permission."}
        except TelegramBadRequest as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool
    async def send_photo(
        chat_id: int,
        photo_url: str,
        caption: str | None = None,
        parse_mode: str | None = "HTML",
        disable_notification: bool = False,
    ) -> ToolResult:
        """Send a photo to a Telegram chat."""
        if not ctx.is_chat_allowed(chat_id):
            return {"ok": False, "error": f"Chat {chat_id} is not allowed."}

        try:
            msg = await ctx.bot.send_photo(
                chat_id=chat_id,
                photo=photo_url,
                caption=caption,
                parse_mode=_normalize_parse_mode(parse_mode),
                disable_notification=disable_notification,
            )
            return {"ok": True, "message_id": msg.message_id, "chat_id": msg.chat.id}
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        except (TelegramBadRequest, TelegramForbiddenError) as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool
    async def forward_message(
        to_chat_id: int,
        from_chat_id: int,
        message_id: int,
        disable_notification: bool = False,
    ) -> ToolResult:
        """Forward an existing message from one chat to another."""
        if not ctx.is_chat_allowed(to_chat_id):
            return {"ok": False, "error": f"Chat {to_chat_id} is not allowed."}

        try:
            msg = await ctx.bot.forward_message(
                chat_id=to_chat_id,
                from_chat_id=from_chat_id,
                message_id=message_id,
                disable_notification=disable_notification,
            )
            return {"ok": True, "message_id": msg.message_id}
        except (TelegramBadRequest, TelegramForbiddenError) as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool
    async def delete_message(chat_id: int, message_id: int) -> ToolResult:
        """Delete a message from a chat."""
        if not ctx.is_chat_allowed(chat_id):
            return {"ok": False, "error": f"Chat {chat_id} is not allowed."}

        try:
            await ctx.bot.delete_message(chat_id=chat_id, message_id=message_id)
            return {"ok": True}
        except (TelegramBadRequest, TelegramForbiddenError) as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool
    async def pin_message(
        chat_id: int,
        message_id: int,
        disable_notification: bool = False,
    ) -> ToolResult:
        """Pin a message in a chat."""
        if not ctx.is_chat_allowed(chat_id):
            return {"ok": False, "error": f"Chat {chat_id} is not allowed."}

        try:
            await ctx.bot.pin_chat_message(
                chat_id=chat_id,
                message_id=message_id,
                disable_notification=disable_notification,
            )
            return {"ok": True}
        except (TelegramBadRequest, TelegramForbiddenError) as exc:
            return {"ok": False, "error": str(exc)}
