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

Events:

- `subscribe_events`
- `unsubscribe_events`

Broadcast:

- `broadcast` when `enable_broadcast=True`

## MCP Resources

Read-only data exposed to AI agents without tool calls:

| URI | Description |
|---|---|
| `telegram://bot/info` | Bot metadata (username, capabilities) |
| `telegram://config` | Server configuration and allowed chat IDs |
| `telegram://chats` | Active chats the bot has seen (requires middleware) |
| `telegram://chats/{chat_id}/history` | Recent message history for a chat |
| `telegram://events/queue` | Real-time event queue (requires EventManager) |

Resources require `MCPMiddleware` to be attached for chat tracking and message history.

## MCP Prompts

Ready-made workflows that give AI agents structured context instead of raw tools:

| Prompt | Arguments | Description |
|---|---|---|
| `moderation_prompt` | `chat_id`, `user_id`, `reason` | Review user behavior with message history and suggest moderation action |
| `announcement_prompt` | `topic`, `audience?`, `tone?` | Draft a Telegram announcement with formatting guidelines |
| `user_report_prompt` | `chat_id`, `user_id` | Compile a comprehensive user activity report |

Prompts that access chat data require `MCPMiddleware` for message history and `allowed_chat_ids` for access control.

## Real-time Event Streaming

AI agents can receive Telegram events in real time instead of polling:

| Component | Type | Description |
|---|---|---|
| `subscribe_events` | Tool | Subscribe to events with chat/type filters |
| `unsubscribe_events` | Tool | Remove a subscription by ID |
| `telegram://events/queue` | Resource | Read queued events with auto-incrementing IDs |

```python
from aiogram_mcp import AiogramMCP, EventManager, MCPMiddleware

event_manager = EventManager()
middleware = MCPMiddleware(event_manager=event_manager)
dp.message.middleware(middleware)

mcp = AiogramMCP(
    bot=bot, dp=dp,
    middleware=middleware,
    event_manager=event_manager,
)
```

When subscribed, AI clients receive MCP `notifications/resources/updated` on new events and can read the queue resource to get event data. Event types: `message`, `command`.

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

Use `MCPMiddleware` to track chats, users, and message history for MCP resources:

```python
from aiogram_mcp import AiogramMCP, MCPMiddleware

tracker = MCPMiddleware(history_size=50)
dp.message.middleware(tracker)

mcp = AiogramMCP(bot=bot, dp=dp, middleware=tracker, enable_broadcast=True)
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
