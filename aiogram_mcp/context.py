"""Shared runtime context for MCP tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from aiogram import Bot, Dispatcher

if TYPE_CHECKING:
    from .events import EventManager
    from .middleware import MCPMiddleware


@dataclass(slots=True)
class BotContext:
    """Dependencies shared by all tool handlers."""

    bot: Bot
    dp: Dispatcher
    allowed_chat_ids: list[int] | None = None
    middleware: MCPMiddleware | None = None
    event_manager: EventManager | None = None

    def is_chat_allowed(self, chat_id: int) -> bool:
        """Return whether the MCP server may act on a chat."""
        if self.allowed_chat_ids is None:
            return True
        return chat_id in self.allowed_chat_ids
