"""Core AiogramMCP server implementation."""

from __future__ import annotations

import asyncio
import logging
from contextlib import suppress

from aiogram import Bot, Dispatcher
from fastmcp import FastMCP

from .context import BotContext
from .events import EventManager
from .middleware import MCPMiddleware
from .prompts import register_prompts
from .resources import register_resources
from .tools.broadcast import register_broadcast_tools
from .tools.chats import register_chat_tools
from .tools.events import register_event_tools
from .tools.interactive import register_interactive_tools
from .tools.media import register_media_tools
from .tools.messaging import register_messaging_tools
from .tools.users import register_user_tools

logger = logging.getLogger(__name__)


class AiogramMCP:
    """Expose an existing aiogram bot as an MCP server."""

    def __init__(
        self,
        bot: Bot,
        dp: Dispatcher,
        name: str = "aiogram-mcp",
        allowed_chat_ids: list[int] | None = None,
        enable_broadcast: bool = False,
        max_broadcast_recipients: int = 100,
        middleware: MCPMiddleware | None = None,
        event_manager: EventManager | None = None,
    ) -> None:
        self.bot = bot
        self.dp = dp
        self.name = name
        self.allowed_chat_ids = allowed_chat_ids
        self.enable_broadcast = enable_broadcast
        self.max_broadcast_recipients = max_broadcast_recipients

        self._ctx = BotContext(
            bot=bot,
            dp=dp,
            allowed_chat_ids=allowed_chat_ids,
            middleware=middleware,
            event_manager=event_manager,
        )
        self._mcp = FastMCP(
            name=name,
            instructions=(
                "You are connected to a Telegram bot via aiogram-mcp. "
                "You can send messages, inspect users and chats, and perform "
                "administrative actions. Confirm destructive actions first."
            ),
        )

        self._register_tools()
        logger.info("AiogramMCP initialized with server name '%s'", name)

    def _register_tools(self) -> None:
        register_messaging_tools(self._mcp, self._ctx)
        register_user_tools(self._mcp, self._ctx)
        register_chat_tools(self._mcp, self._ctx)
        register_resources(self._mcp, self._ctx)
        register_prompts(self._mcp, self._ctx)
        register_event_tools(self._mcp, self._ctx)
        register_interactive_tools(self._mcp, self._ctx)
        register_media_tools(self._mcp, self._ctx)

        if self.enable_broadcast:
            register_broadcast_tools(
                self._mcp,
                self._ctx,
                max_recipients=self.max_broadcast_recipients,
            )

    async def run_stdio(self) -> None:
        """Run the MCP server over stdio."""
        logger.info("Starting aiogram-mcp in stdio mode")
        await self._mcp.run_async(transport="stdio")

    async def run_sse(self, host: str = "0.0.0.0", port: int = 8080) -> None:
        """Run the MCP server over SSE."""
        logger.info("Starting aiogram-mcp in SSE mode on %s:%s", host, port)
        await self._mcp.run_async(transport="sse", host=host, port=port)

    async def run_alongside_bot(
        self,
        *,
        transport: str = "stdio",
        host: str = "0.0.0.0",
        port: int = 8080,
    ) -> None:
        """Run bot polling and MCP server concurrently."""
        if transport not in {"stdio", "sse"}:
            raise ValueError("transport must be 'stdio' or 'sse'")

        if transport == "stdio":
            mcp_task = asyncio.create_task(self.run_stdio())
        else:
            mcp_task = asyncio.create_task(self.run_sse(host=host, port=port))

        bot_task = asyncio.create_task(self.dp.start_polling(self.bot))

        try:
            logger.info("Running aiogram polling and MCP server concurrently")
            await asyncio.gather(bot_task, mcp_task)
        finally:
            for task in (bot_task, mcp_task):
                if not task.done():
                    task.cancel()
            with suppress(asyncio.CancelledError):
                await asyncio.gather(bot_task, mcp_task)
            await self.bot.session.close()

    @property
    def fastmcp(self) -> FastMCP:
        """Expose the underlying FastMCP instance for custom tools."""
        return self._mcp
