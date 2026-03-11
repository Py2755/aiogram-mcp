"""Middleware utilities exposed by the package."""

from __future__ import annotations

from collections import deque
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

if TYPE_CHECKING:
    from .events import EventManager


class MCPMiddleware(BaseMiddleware):
    """Track active chats, users, and message history for MCP resources."""

    def __init__(
        self,
        history_size: int = 50,
        event_manager: EventManager | None = None,
    ) -> None:
        self.history_size = history_size
        self.event_manager = event_manager
        self.active_chat_ids: set[int] = set()
        self.active_user_ids: set[int] = set()
        self.message_history: dict[int, deque[dict[str, Any]]] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        chat = getattr(event, "chat", None)
        chat_id: int | None = None
        if chat is not None and getattr(chat, "id", None) is not None:
            chat_id = chat.id
            self.active_chat_ids.add(chat_id)

        user = getattr(event, "from_user", None)
        if user is not None and getattr(user, "id", None) is not None:
            self.active_user_ids.add(user.id)

        # Cache text messages for history resource
        text = getattr(event, "text", None)
        if chat_id is not None and text is not None:
            if chat_id not in self.message_history:
                self.message_history[chat_id] = deque(maxlen=self.history_size)
            event_date = getattr(event, "date", None)
            self.message_history[chat_id].append({
                "message_id": getattr(event, "message_id", None),
                "from_user_id": user.id if user else None,
                "from_username": getattr(user, "username", None) if user else None,
                "text": text,
                "date": event_date.isoformat() if event_date else None,
            })

            # Push event to EventManager for real-time streaming
            if self.event_manager is not None:
                event_type = "command" if text.startswith("/") else "message"
                await self.event_manager.push_event({
                    "type": event_type,
                    "chat_id": chat_id,
                    "from_user_id": user.id if user else None,
                    "from_username": (
                        getattr(user, "username", None) if user else None
                    ),
                    "text": text,
                    "message_id": getattr(event, "message_id", None),
                    "date": event_date.isoformat() if event_date else None,
                })

        return await handler(event, data)
