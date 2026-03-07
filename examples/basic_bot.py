"""Basic example: existing aiogram bot + aiogram-mcp running side by side."""

from __future__ import annotations

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from aiogram_mcp import AiogramMCP, MCPMiddleware

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.environ["BOT_TOKEN"]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

mcp_middleware = MCPMiddleware()
dp.message.middleware(mcp_middleware)


@dp.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "Hello! This bot is running normally, and it is also exposed over MCP."
    )


@dp.message(F.text)
async def echo(message: Message) -> None:
    await message.answer(f"You said: {message.text}")


mcp = AiogramMCP(
    bot=bot,
    dp=dp,
    name="my-telegram-bot",
    middleware=mcp_middleware,
)


async def main() -> None:
    await mcp.run_alongside_bot(transport="stdio")


if __name__ == "__main__":
    asyncio.run(main())
