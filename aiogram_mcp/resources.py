"""MCP Resources — expose bot data as read-only context."""

from __future__ import annotations

import json
from contextlib import suppress
from typing import Any

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from fastmcp import FastMCP

from .context import BotContext


def register_resources(mcp: FastMCP, ctx: BotContext) -> None:
    """Register all MCP resources on the FastMCP server."""

    @mcp.resource("telegram://bot/info")
    async def bot_info() -> str:
        """Metadata about the connected Telegram bot."""
        me = await ctx.bot.get_me()
        return json.dumps({
            "id": me.id,
            "username": me.username,
            "first_name": me.first_name,
            "is_bot": me.is_bot,
            "can_join_groups": me.can_join_groups,
            "can_read_all_group_messages": me.can_read_all_group_messages,
            "supports_inline_queries": me.supports_inline_queries,
        })

    @mcp.resource("telegram://config")
    async def config() -> str:
        """Current aiogram-mcp server configuration."""
        return json.dumps({
            "server_name": mcp.name,
            "allowed_chat_ids": ctx.allowed_chat_ids,
        })

    @mcp.resource("telegram://chats")
    async def chats() -> str:
        """List of active Telegram chats the bot has seen."""
        if ctx.middleware is None:
            return json.dumps({
                "chats": [],
                "note": "MCPMiddleware is not attached. No chat tracking available.",
            })

        result: list[dict[str, Any]] = []
        for chat_id in ctx.middleware.active_chat_ids:
            if not ctx.is_chat_allowed(chat_id):
                continue
            try:
                chat = await ctx.bot.get_chat(chat_id)
                count = None
                with suppress(TelegramBadRequest, TelegramForbiddenError):
                    count = await ctx.bot.get_chat_member_count(chat_id)
                result.append({
                    "id": chat.id,
                    "type": getattr(chat.type, "value", str(chat.type)),
                    "title": getattr(chat, "title", None),
                    "username": getattr(chat, "username", None),
                    "member_count": count,
                })
            except (TelegramBadRequest, TelegramForbiddenError):
                continue

        return json.dumps({"chats": result})

    @mcp.resource("telegram://chats/{chat_id}/history")
    async def chat_history(chat_id: str) -> str:
        """Recent message history for a specific chat."""
        cid = int(chat_id)

        if not ctx.is_chat_allowed(cid):
            return json.dumps({
                "ok": False,
                "error": f"Chat {cid} is not in allowed_chat_ids.",
            })

        if ctx.middleware is None:
            return json.dumps({
                "messages": [],
                "note": "MCPMiddleware is not attached. No history available.",
            })

        messages = list(ctx.middleware.message_history.get(cid, []))
        return json.dumps({"chat_id": cid, "messages": messages})

    @mcp.resource("telegram://events/queue")
    async def events_queue() -> str:
        """Real-time event queue from Telegram.

        Returns recent events (messages, commands) received by the bot.
        Use subscribe_events tool to get push notifications when new events arrive.
        Each event has an 'id' field — use it to track which events you've seen.
        """
        if ctx.event_manager is None:
            return json.dumps({
                "events": [],
                "count": 0,
                "note": "EventManager is not configured. No event streaming available.",
            })

        events = ctx.event_manager.get_events()
        return json.dumps({"events": events, "count": len(events)})

    @mcp.resource("telegram://files/{file_id}")
    async def file_info(file_id: str) -> str:
        """Metadata for a Telegram file.

        Returns file_id, file_unique_id, file_size, and file_path.
        Use the file_path with the Telegram Bot API download endpoint to retrieve the file.
        """
        try:
            f = await ctx.bot.get_file(file_id)
            return json.dumps({
                "file_id": f.file_id,
                "file_unique_id": f.file_unique_id,
                "file_size": f.file_size,
                "file_path": f.file_path,
            })
        except (TelegramBadRequest, TelegramForbiddenError) as exc:
            return json.dumps({"ok": False, "error": str(exc)})
