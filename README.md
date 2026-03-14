# aiogram-mcp

[![CI](https://github.com/Py2755/aiogram-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/Py2755/aiogram-mcp/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![PyPI version](https://img.shields.io/pypi/v/aiogram-mcp.svg)](https://pypi.org/project/aiogram-mcp/)

**Connect your Telegram bot to AI agents via the Model Context Protocol.**

`aiogram-mcp` turns any [aiogram](https://github.com/aiogram/aiogram) bot into an [MCP](https://modelcontextprotocol.io/) server. AI clients like Claude Desktop can then send messages, read chat history, build interactive menus, and react to events in real time — all through your existing bot, without rewriting a single handler.

## Why aiogram-mcp?

Most Telegram MCP servers are thin wrappers with 3-5 tools. `aiogram-mcp` goes further:

- **30 tools** — messaging, rich media, moderation, interactive keyboards, event subscriptions, broadcasting
- **7 resources** — bot info, config, chat lists, message history, event queue, file metadata, audit log
- **3 prompts** — ready-made moderation, announcement, and user report workflows
- **Structured output** — every tool returns typed Pydantic models with `outputSchema` for programmatic parsing
- **Real-time events** — the bot pushes Telegram events to AI clients via MCP notifications (no polling)
- **Interactive messages** — AI agents create inline keyboard menus, handle button presses, edit messages
- **Rate limiting** — built-in token bucket prevents Telegram 429 errors
- **Permission levels** — restrict AI agents to read-only, messaging, moderation, or full admin access
- **Audit logging** — track every tool invocation with timestamps and arguments
- **Zero rewrite** — add 5 lines to your existing bot, keep all your handlers

## How It Works

```
Telegram users                Your aiogram bot              AI agent (Claude Desktop)
      |                             |                              |
      |  send messages, tap buttons |                              |
      | --------------------------> |                              |
      |                             |  MCP server (stdio or SSE)   |
      |                             | <------------------------->  |
      |                             |  tools / resources / events  |
      |                             |                              |
      |  bot replies, shows menus   |   send_message, edit, ban    |
      | <-------------------------- | <--------------------------- |
```

The bot runs normally for Telegram users. The MCP server runs alongside it, giving AI agents access to the same bot via tools and resources.

## Installation

```bash
pip install aiogram-mcp
```

Requires Python 3.10+ and aiogram 3.20+.

## Quickstart

### 1. Add aiogram-mcp to your bot

```python
import asyncio
from aiogram import Bot, Dispatcher
from aiogram_mcp import AiogramMCP, EventManager, MCPMiddleware

bot = Bot(token="YOUR_BOT_TOKEN")
dp = Dispatcher()

# Middleware tracks chats, users, message history, and events
event_manager = EventManager()
middleware = MCPMiddleware(event_manager=event_manager)
dp.message.middleware(middleware)
dp.callback_query.middleware(middleware)  # for interactive buttons

# Register your normal handlers here
# @dp.message(...)
# async def my_handler(message): ...

# Create the MCP server
mcp = AiogramMCP(
    bot=bot,
    dp=dp,
    name="my-bot",
    middleware=middleware,
    event_manager=event_manager,
    allowed_chat_ids=[123456789],  # optional: restrict which chats AI can access
)

async def main():
    await mcp.run_alongside_bot(transport="stdio")

asyncio.run(main())
```

### 2. Connect Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "my-telegram-bot": {
      "command": "python",
      "args": ["path/to/your/bot.py"],
      "env": {
        "BOT_TOKEN": "123456:ABC-DEF..."
      }
    }
  }
}
```

Now Claude can send messages, read history, create button menus, and react to events in your Telegram bot.

## Built-in Tools

### Messaging (5 tools)

| Tool | Description |
|------|-------------|
| `send_message` | Send text with HTML/Markdown formatting |
| `send_photo` | Send a photo by URL with optional caption |
| `forward_message` | Forward a message between chats |
| `delete_message` | Delete a message |
| `pin_message` | Pin a message in a chat |

### Interactive Messages (3 tools)

| Tool | Description |
|------|-------------|
| `send_interactive_message` | Send a message with inline keyboard buttons (callback or URL) |
| `edit_message` | Edit text and/or keyboard of an existing message |
| `answer_callback_query` | Respond to a button press with a toast or alert |

### Users (3 tools)

| Tool | Description |
|------|-------------|
| `get_bot_info` | Get bot metadata (username, capabilities) |
| `get_chat_member_info` | Get a user's role and profile in a chat |
| `get_user_profile_photos` | Get a user's profile photos |

### Chats (6 tools)

| Tool | Description |
|------|-------------|
| `get_chat_info` | Get chat metadata (title, type, description) |
| `get_chat_members_count` | Get number of members in a chat |
| `ban_user` | Ban a user (permanent or temporary) |
| `unban_user` | Unban a user |
| `set_chat_title` | Change the chat title |
| `set_chat_description` | Change the chat description |

### Rich Media (10 tools)

| Tool | Description |
|------|-------------|
| `send_document` | Send a file/document by URL with optional caption |
| `send_voice` | Send a voice message by URL |
| `send_video` | Send a video by URL with optional caption |
| `send_animation` | Send a GIF/animation by URL |
| `send_audio` | Send audio/music by URL with performer and title |
| `send_sticker` | Send a sticker by file_id or URL |
| `send_video_note` | Send a round video note by URL |
| `send_contact` | Send a contact with phone number and name |
| `send_location` | Send a geolocation pin |
| `send_poll` | Create a poll with multiple options |

### Events (2 tools)

| Tool | Description |
|------|-------------|
| `subscribe_events` | Subscribe to real-time events with chat/type filters |
| `unsubscribe_events` | Remove a subscription |

### Broadcast (1 tool, opt-in)

| Tool | Description |
|------|-------------|
| `broadcast` | Send a message to multiple chats (requires `enable_broadcast=True`) |

## MCP Resources

Read-only data that AI agents can access without calling tools:

| URI | Description |
|-----|-------------|
| `telegram://bot/info` | Bot username, ID, and capabilities |
| `telegram://config` | Server name and allowed chat IDs |
| `telegram://chats` | List of active chats with metadata |
| `telegram://chats/{chat_id}/history` | Last 50 messages in a chat |
| `telegram://events/queue` | Event queue with auto-incrementing IDs |
| `telegram://files/{file_id}` | File metadata (size, path, unique ID) |
| `telegram://audit/log` | Audit log of tool invocations (opt-in) |

## MCP Prompts

Pre-built workflows that give AI agents structured context:

| Prompt | Arguments | What it does |
|--------|-----------|-------------|
| `moderation_prompt` | `chat_id`, `user_id`, `reason` | Fetches user info + message history, suggests warn/mute/ban |
| `announcement_prompt` | `topic`, `audience?`, `tone?` | Drafts a formatted Telegram announcement |
| `user_report_prompt` | `chat_id`, `user_id` | Compiles a full user activity report |

## Real-time Event Streaming

AI agents don't need to poll. The bot pushes events automatically:

```
Telegram message arrives
    → MCPMiddleware captures it
        → EventManager stores it (type: "message", "command", or "callback_query")
            → MCP notification sent to subscribed clients
                → AI agent reads telegram://events/queue
```

The AI agent calls `subscribe_events` once, then receives push notifications whenever new events match its filters.

## Interactive Messages

AI agents can build full interactive UIs in Telegram — menus, confirmations, multi-step wizards:

**The AI agent sends a message with buttons:**
```
┌─────────────────────────┐
│ Confirm deployment?     │
│                         │
│  [✅ Yes]  [❌ No]      │
│  [📖 View docs]        │
└─────────────────────────┘
```

**User taps a button → event appears in the queue → AI agent reacts:**
```
┌─────────────────────────┐
│ ✅ Deployed!            │
│                         │
│  [📋 View logs]        │
└─────────────────────────┘
```

The bot needs `dp.callback_query.middleware(middleware)` to capture button presses.

## Safety Controls

```python
mcp = AiogramMCP(
    bot=bot,
    dp=dp,
    allowed_chat_ids=[123456789, -1001234567890],  # restrict AI access
    enable_broadcast=True,            # opt-in for broadcast tool
    max_broadcast_recipients=500,     # safety limit
)
```

- **`allowed_chat_ids`** — AI can only interact with listed chats. Default: all chats.
- **`enable_broadcast`** — broadcast tool is disabled by default as a safety measure.
- **`max_broadcast_recipients`** — caps the number of chats in a single broadcast.

## Advanced Configuration

### Rate Limiting

```python
mcp = AiogramMCP(
    bot=bot, dp=dp,
    rate_limit=30,  # requests/sec (default), 0 to disable
)
```

Built-in token bucket rate limiter prevents Telegram 429 errors. All outgoing API calls are automatically paced.

### Permission Levels

```python
mcp = AiogramMCP(
    bot=bot, dp=dp,
    permission_level="messaging",  # read + messaging tools only
)
```

| Level | Access |
|-------|--------|
| `read` | Bot info, chat info, user profiles |
| `messaging` | Read + send messages, photos, media, interactive messages |
| `moderation` | Messaging + delete, pin, ban, unban, chat settings |
| `admin` | Full access including broadcast and event subscriptions |

### Audit Log

```python
mcp = AiogramMCP(
    bot=bot, dp=dp,
    enable_audit=True,
    audit_log_size=1000,
)
```

Every tool invocation is logged. Access via `telegram://audit/log` resource.

## Examples

| Example | Transport | Features |
|---------|-----------|----------|
| [basic_bot.py](examples/basic_bot.py) | stdio | Full setup with middleware, events, and callback tracking |
| [incident_alert_bot.py](examples/incident_alert_bot.py) | SSE | Broadcast-enabled ops bot for incident notifications |

## Development

```bash
git clone https://github.com/Py2755/aiogram-mcp.git
cd aiogram-mcp
pip install -e ".[dev]"

pytest -v          # ~228 tests
ruff check aiogram_mcp tests examples
mypy aiogram_mcp   # strict mode
```

## License

MIT. See [LICENSE](LICENSE).
