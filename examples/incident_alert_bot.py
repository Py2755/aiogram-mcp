"""Incident alerting bot example for aiogram-mcp.

This bot represents a practical operations workflow:
- users subscribe to outage notifications
- the bot keeps its normal Telegram UX
- an MCP client can inspect chats and send targeted updates during incidents
"""

from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from aiogram_mcp import AiogramMCP, MCPMiddleware

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

tracker = MCPMiddleware()
dp.message.middleware(tracker)


@dp.message(Command("start"))
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Service Status Bot\n\n"
        "Commands:\n"
        "/subscribe - opt into incident alerts\n"
        "/status - get the current platform status"
    )


@dp.message(Command("subscribe"))
async def cmd_subscribe(message: Message) -> None:
    await message.answer(
        "You're subscribed. During an outage, responders can notify you through MCP."
    )


@dp.message(Command("status"))
async def cmd_status(message: Message) -> None:
    await message.answer(
        "All systems operational.\n"
        "If anything changes, this bot can push an incident update automatically."
    )


@dp.message(F.text)
async def fallback(message: Message) -> None:
    await message.answer(
        "Use /status for the current state or /subscribe to receive incident alerts."
    )


mcp = AiogramMCP(
    bot=bot,
    dp=dp,
    name="service-status-bot",
    enable_broadcast=True,
    max_broadcast_recipients=1000,
)


async def main() -> None:
    await mcp.run_alongside_bot(transport="sse", port=8080)


if __name__ == "__main__":
    asyncio.run(main())
