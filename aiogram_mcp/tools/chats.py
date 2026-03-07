"""Chat tools for moderation and inspection."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from fastmcp import FastMCP

from ..context import BotContext

ToolResult = dict[str, Any]


def register_chat_tools(mcp: FastMCP, ctx: BotContext) -> None:
    @mcp.tool
    async def get_chat_info(chat_id: int) -> ToolResult:
        """Get details about a chat."""
        try:
            chat = await ctx.bot.get_chat(chat_id)
            member_count = None
            try:
                member_count = await ctx.bot.get_chat_member_count(chat_id=chat_id)
            except (TelegramBadRequest, TelegramForbiddenError):
                member_count = None

            return {
                "ok": True,
                "id": chat.id,
                "type": getattr(chat.type, "value", str(chat.type)),
                "title": getattr(chat, "title", None),
                "username": getattr(chat, "username", None),
                "description": getattr(chat, "description", None),
                "member_count": member_count,
                "is_forum": getattr(chat, "is_forum", False),
            }
        except (TelegramBadRequest, TelegramForbiddenError) as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool
    async def get_chat_members_count(chat_id: int) -> ToolResult:
        """Get the number of members in a chat."""
        try:
            count = await ctx.bot.get_chat_member_count(chat_id=chat_id)
            return {"ok": True, "count": count}
        except (TelegramBadRequest, TelegramForbiddenError) as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool
    async def ban_user(
        chat_id: int,
        user_id: int,
        ban_duration_hours: int | None = None,
        revoke_messages: bool = False,
    ) -> ToolResult:
        """Ban a user from a chat."""
        if not ctx.is_chat_allowed(chat_id):
            return {"ok": False, "error": f"Chat {chat_id} is not allowed."}

        until_date = None
        if ban_duration_hours:
            until_date = datetime.now(timezone.utc) + timedelta(hours=ban_duration_hours)

        try:
            await ctx.bot.ban_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                until_date=until_date,
                revoke_messages=revoke_messages,
            )
            return {
                "ok": True,
                "user_id": user_id,
                "permanent": until_date is None,
                "until": until_date.isoformat() if until_date else None,
            }
        except (TelegramBadRequest, TelegramForbiddenError) as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool
    async def unban_user(
        chat_id: int,
        user_id: int,
        only_if_banned: bool = True,
    ) -> ToolResult:
        """Unban a previously banned user."""
        if not ctx.is_chat_allowed(chat_id):
            return {"ok": False, "error": f"Chat {chat_id} is not allowed."}

        try:
            await ctx.bot.unban_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                only_if_banned=only_if_banned,
            )
            return {"ok": True, "user_id": user_id}
        except (TelegramBadRequest, TelegramForbiddenError) as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool
    async def set_chat_title(chat_id: int, title: str) -> ToolResult:
        """Change the title of a group or channel."""
        if not ctx.is_chat_allowed(chat_id):
            return {"ok": False, "error": f"Chat {chat_id} is not allowed."}

        try:
            await ctx.bot.set_chat_title(chat_id=chat_id, title=title)
            return {"ok": True, "new_title": title}
        except (TelegramBadRequest, TelegramForbiddenError) as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool
    async def set_chat_description(chat_id: int, description: str) -> ToolResult:
        """Change the description of a group or channel."""
        if not ctx.is_chat_allowed(chat_id):
            return {"ok": False, "error": f"Chat {chat_id} is not allowed."}

        try:
            await ctx.bot.set_chat_description(chat_id=chat_id, description=description)
            return {"ok": True}
        except (TelegramBadRequest, TelegramForbiddenError) as exc:
            return {"ok": False, "error": str(exc)}
