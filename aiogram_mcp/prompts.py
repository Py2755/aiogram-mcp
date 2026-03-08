"""MCP Prompts — ready-made workflows for AI agents."""

from __future__ import annotations

import json
from contextlib import suppress
from typing import Any

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from fastmcp import FastMCP

from .context import BotContext


def register_prompts(mcp: FastMCP, ctx: BotContext) -> None:
    """Register all MCP prompts on the FastMCP server."""

    @mcp.prompt
    async def moderation_prompt(chat_id: str, user_id: str, reason: str) -> str:
        """Review a user's behavior and decide on moderation action.

        Fetches user info, chat context, and recent messages to help
        the AI agent make an informed moderation decision.
        """
        cid = int(chat_id)
        uid = int(user_id)

        if not ctx.is_chat_allowed(cid):
            return json.dumps({
                "error": f"Chat {cid} is not in allowed_chat_ids.",
            })

        # Fetch user and chat info
        user_info: dict[str, Any] = {"user_id": uid}
        chat_info: dict[str, Any] = {"chat_id": cid}

        with suppress(TelegramBadRequest, TelegramForbiddenError):
            chat = await ctx.bot.get_chat(cid)
            chat_info.update({
                "title": getattr(chat, "title", None),
                "type": getattr(chat.type, "value", str(chat.type)),
            })

        with suppress(TelegramBadRequest, TelegramForbiddenError):
            member = await ctx.bot.get_chat_member(cid, uid)
            user_info.update({
                "first_name": getattr(member.user, "first_name", None),
                "last_name": getattr(member.user, "last_name", None),
                "username": getattr(member.user, "username", None),
                "language_code": getattr(member.user, "language_code", None),
                "status": getattr(member.status, "value", str(member.status)),
            })

        # Collect recent messages from this user
        recent_messages: list[dict[str, Any]] = []
        if ctx.middleware is not None:
            for msg in ctx.middleware.message_history.get(cid, []):
                if msg.get("from_user_id") == uid:
                    recent_messages.append(msg)

        return (
            "You are a chat moderator. Review the following information and "
            "decide on the appropriate action.\n\n"
            f"## Chat\n{json.dumps(chat_info, indent=2)}\n\n"
            f"## User\n{json.dumps(user_info, indent=2)}\n\n"
            f"## Reason for review\n{reason}\n\n"
            f"## Recent messages from this user\n"
            f"{json.dumps(recent_messages, indent=2)}\n\n"
            "## Available actions\n"
            "- **Warn**: send a warning message via `send_message`\n"
            "- **Mute**: restrict the user (not yet implemented)\n"
            "- **Ban**: remove the user via `ban_user`\n"
            "- **Dismiss**: no action needed\n\n"
            "Explain your reasoning before choosing an action."
        )

    @mcp.prompt
    async def announcement_prompt(
        topic: str, audience: str = "all members", tone: str = "friendly"
    ) -> str:
        """Draft a Telegram announcement message.

        Provides a structured template with formatting guidelines
        to help the AI agent compose an effective announcement.
        """
        return (
            "You are a Telegram bot assistant. Draft an announcement message "
            "using the following brief.\n\n"
            f"## Topic\n{topic}\n\n"
            f"## Target audience\n{audience}\n\n"
            f"## Desired tone\n{tone}\n\n"
            "## Telegram formatting guidelines\n"
            "- Use HTML tags: <b>bold</b>, <i>italic</i>, <code>code</code>\n"
            "- Use `parse_mode=\"HTML\"` when sending via `send_message`\n"
            "- Keep the message concise (under 4096 characters)\n"
            "- Consider setting `disable_notification=True` for non-urgent posts\n\n"
            "## Suggested structure\n"
            "1. Greeting or attention-grabber\n"
            "2. Main announcement body\n"
            "3. Call to action or next steps\n\n"
            "Return ONLY the message text ready to be sent."
        )

    @mcp.prompt
    async def user_report_prompt(chat_id: str, user_id: str) -> str:
        """Generate a comprehensive report about a user in a chat.

        Fetches profile data, chat membership, and message history
        to compile a detailed user activity report.
        """
        cid = int(chat_id)
        uid = int(user_id)

        if not ctx.is_chat_allowed(cid):
            return json.dumps({
                "error": f"Chat {cid} is not in allowed_chat_ids.",
            })

        # Fetch user and chat info
        user_info: dict[str, Any] = {"user_id": uid}
        chat_info: dict[str, Any] = {"chat_id": cid}

        with suppress(TelegramBadRequest, TelegramForbiddenError):
            chat = await ctx.bot.get_chat(cid)
            chat_info.update({
                "title": getattr(chat, "title", None),
                "type": getattr(chat.type, "value", str(chat.type)),
            })

        with suppress(TelegramBadRequest, TelegramForbiddenError):
            member = await ctx.bot.get_chat_member(cid, uid)
            user_info.update({
                "first_name": getattr(member.user, "first_name", None),
                "last_name": getattr(member.user, "last_name", None),
                "username": getattr(member.user, "username", None),
                "language_code": getattr(member.user, "language_code", None),
                "is_bot": getattr(member.user, "is_bot", None),
                "is_premium": getattr(member.user, "is_premium", None),
                "status": getattr(member.status, "value", str(member.status)),
            })

        # Profile photos count
        photos_count = 0
        with suppress(TelegramBadRequest, TelegramForbiddenError):
            photos = await ctx.bot.get_user_profile_photos(uid)
            photos_count = photos.total_count

        # Message activity
        recent_messages: list[dict[str, Any]] = []
        message_count = 0
        last_message_date: str | None = None
        if ctx.middleware is not None:
            for msg in ctx.middleware.message_history.get(cid, []):
                if msg.get("from_user_id") == uid:
                    message_count += 1
                    last_message_date = msg.get("date")
                    recent_messages.append(msg)

        activity: dict[str, Any] = {
            "message_count": message_count,
            "last_message_date": last_message_date,
        }

        return (
            "You are an analyst. Compile a user activity report from the "
            "following data.\n\n"
            f"## Chat\n{json.dumps(chat_info, indent=2)}\n\n"
            f"## User profile\n{json.dumps(user_info, indent=2)}\n\n"
            f"## Profile photos\nTotal: {photos_count}\n\n"
            f"## Message activity\n{json.dumps(activity, indent=2)}\n\n"
            f"## Recent messages\n{json.dumps(recent_messages, indent=2)}\n\n"
            "Summarize the user's profile, role, and activity in this chat."
        )
