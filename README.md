# aiogram-mcp

[![CI](https://github.com/Py2755/aiogram-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Py2755/aiogram-mcp/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/aiogram-mcp.svg)](https://pypi.org/project/aiogram-mcp/)

MCP server middleware for aiogram Telegram bots.

`aiogram-mcp` lets you expose an existing [aiogram](https://github.com/aiogram/aiogram) bot to [MCP](https://modelcontextprotocol.io/) clients such as Claude Desktop without rewriting handlers, routers, or business logic.

## Status

**Beta** — the core API is stable but may change before 1.0.

## Installation

```bash
pip install aiogram-mcp
```

Requirements:

- Python 3.10+
- aiogram 3.20+

## Quickstart

```python
from aiogram import Bot, Dispatcher
from aiogram_mcp import AiogramMCP

bot = Bot(token="YOUR_BOT_TOKEN")
dp = Dispatcher()

# Register your normal handlers here.

mcp = AiogramMCP(bot=bot, dp=dp)
await mcp.run_alongside_bot(transport="stdio")
```

Available transports:

- `stdio` for Claude Desktop and local MCP clients
- `sse` for remote HTTP-based MCP connections

## Built-in Tools

Messaging:

- `send_message`
- `send_photo`
- `forward_message`
- `delete_message`
- `pin_message`

Users:

- `get_bot_info`
- `get_chat_member_info`
- `get_user_profile_photos`

Chats:

- `get_chat_info`
- `get_chat_members_count`
- `ban_user`
- `unban_user`
- `set_chat_title`
- `set_chat_description`

Broadcast:

- `broadcast` when `enable_broadcast=True`

## Safety Controls

```python
mcp = AiogramMCP(
    bot=bot,
    dp=dp,
    name="my-bot",
    allowed_chat_ids=[123456789, -1001234567890],
    enable_broadcast=True,
    max_broadcast_recipients=500,
)
```

Use `MCPMiddleware` to track recent chats and build recipient lists:

```python
from aiogram_mcp import AiogramMCP, MCPMiddleware

tracker = MCPMiddleware()
dp.message.middleware(tracker)

mcp = AiogramMCP(bot=bot, dp=dp, enable_broadcast=True)
```

## Development

```bash
pip install -e ".[dev]"
ruff check aiogram_mcp tests examples
mypy aiogram_mcp
pytest -v
```

Project layout:

- `aiogram_mcp/` package source
- `tests/` unit tests
- `examples/` runnable usage examples
- `.github/workflows/ci.yml` GitHub Actions pipeline

## Examples

- [basic_bot.py](examples/basic_bot.py)
- [incident_alert_bot.py](examples/incident_alert_bot.py)

## License

MIT. See [LICENSE](LICENSE).
