"""CLI entry point: python -m aiogram_mcp"""

from __future__ import annotations

import asyncio
import os

from aiogram import Bot, Dispatcher

from .server import AiogramMCP


def main() -> None:
    token = os.environ.get("BOT_TOKEN", "0:inspection-mode")

    bot = Bot(token=token)
    dp = Dispatcher()

    mcp = AiogramMCP(bot=bot, dp=dp)

    asyncio.run(mcp.run_stdio())


if __name__ == "__main__":
    main()
