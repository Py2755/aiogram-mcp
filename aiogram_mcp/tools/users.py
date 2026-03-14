"""User inspection tools."""

from __future__ import annotations

from typing import Any

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from fastmcp import FastMCP

from ..context import BotContext
from ..models import ToolResponse


class BotInfoResult(ToolResponse):
    id: int | None = None
    username: str | None = None
    first_name: str | None = None
    is_bot: bool | None = None
    can_join_groups: bool | None = None
    can_read_all_group_messages: bool | None = None
    supports_inline_queries: bool | None = None


class ChatMemberInfoResult(ToolResponse):
    chat_id: int | None = None
    user_id: int | None = None
    status: str | None = None
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str | None = None
    is_bot: bool | None = None


class UserProfilePhotosResult(ToolResponse):
    user_id: int | None = None
    total_count: int | None = None
    photos: list[list[dict[str, Any]]] | None = None


def register_user_tools(
    mcp: FastMCP, ctx: BotContext, allowed_tools: set[str] | None = None
) -> None:
    if allowed_tools is None or "get_bot_info" in allowed_tools:

        @mcp.tool
        async def get_bot_info() -> BotInfoResult:
            """Return metadata about the current Telegram bot."""
            me = await ctx.bot.get_me()
            return BotInfoResult(
                ok=True,
                id=me.id,
                username=me.username,
                first_name=me.first_name,
                is_bot=me.is_bot,
                can_join_groups=me.can_join_groups,
                can_read_all_group_messages=me.can_read_all_group_messages,
                supports_inline_queries=me.supports_inline_queries,
            )

    if allowed_tools is None or "get_chat_member_info" in allowed_tools:

        @mcp.tool
        async def get_chat_member_info(chat_id: int, user_id: int) -> ChatMemberInfoResult:
            """Return role and user info for a chat member."""
            if not ctx.is_chat_allowed(chat_id):
                return ChatMemberInfoResult(
                    ok=False, error=f"Chat {chat_id} is not allowed."
                )

            try:
                member = await ctx.bot.get_chat_member(chat_id=chat_id, user_id=user_id)
            except (TelegramBadRequest, TelegramForbiddenError) as exc:
                return ChatMemberInfoResult(ok=False, error=str(exc))

            user = member.user
            status = member.status.value if hasattr(member.status, "value") else str(member.status)
            return ChatMemberInfoResult(
                ok=True,
                chat_id=chat_id,
                user_id=user.id,
                status=status,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                language_code=user.language_code,
                is_bot=user.is_bot,
            )

    if allowed_tools is None or "get_user_profile_photos" in allowed_tools:

        @mcp.tool
        async def get_user_profile_photos(
            user_id: int, limit: int = 5
        ) -> UserProfilePhotosResult:
            """Return a lightweight list of Telegram profile photo file IDs."""
            if limit < 1 or limit > 100:
                return UserProfilePhotosResult(
                    ok=False, error="limit must be between 1 and 100."
                )

            try:
                photos = await ctx.bot.get_user_profile_photos(user_id=user_id, limit=limit)
            except (TelegramBadRequest, TelegramForbiddenError) as exc:
                return UserProfilePhotosResult(ok=False, error=str(exc))

            return UserProfilePhotosResult(
                ok=True,
                user_id=user_id,
                total_count=photos.total_count,
                photos=[
                    [
                        {
                            "file_id": size.file_id,
                            "file_unique_id": size.file_unique_id,
                            "width": size.width,
                            "height": size.height,
                            "file_size": size.file_size,
                        }
                        for size in group
                    ]
                    for group in photos.photos
                ],
            )
