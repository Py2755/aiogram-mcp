"""Middleware utilities exposed by the package."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class MCPMiddleware(BaseMiddleware):
    """Track active chats and users for later MCP-driven broadcasts."""

    def __init__(self) -> None:
        self.active_chat_ids: set[int] = set()
        self.active_user_ids: set[int] = set()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        chat = getattr(event, "chat", None)
        if chat is not None and getattr(chat, "id", None) is not None:
            self.active_chat_ids.add(chat.id)

        user = getattr(event, "from_user", None)
        if user is not None and getattr(user, "id", None) is not None:
            self.active_user_ids.add(user.id)

        return await handler(event, data)
