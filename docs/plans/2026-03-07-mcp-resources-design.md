# Phase 1: MCP Resources — Design Document

**Date**: 2026-03-07
**Status**: Approved

## Goal

Add MCP Resources to aiogram-mcp — the first Telegram MCP server to expose
bot data as read-only resources. AI agents get context (bot info, active chats,
message history, config) without tool calls.

## Architecture

**Approach**: Extend existing MCPMiddleware with message caching. New
`resources.py` file registers 4 resources that read data from middleware.

**Data flow**:
```
Telegram → Dispatcher → MCPMiddleware (caches messages)
                                ↓
MCP Client ← FastMCP Resources ← resources.py (reads from middleware)
```

**Files changed**:
- `aiogram_mcp/middleware.py` — add `message_history` deque per chat
- `aiogram_mcp/resources.py` — new file, 4 resource functions
- `aiogram_mcp/server.py` — call `register_resources()` on init
- `aiogram_mcp/context.py` — add optional `middleware` field
- `tests/test_core.py` — ~15-20 new tests

## Resources

### `telegram://bot/info`
- Calls `bot.get_me()`, returns bot metadata
- Fields: id, username, first_name, is_bot, permissions

### `telegram://chats`
- Reads `middleware.active_chat_ids`
- For each chat: calls `bot.get_chat()` + `bot.get_chat_member_count()`
- Returns: list of {id, type, title, username, member_count}
- Respects `allowed_chat_ids` filter

### `telegram://chats/{chat_id}/history`
- Reads `middleware.message_history[chat_id]`
- Returns last N messages: {message_id, from_user_id, from_username, text, date}
- Default 50 messages per chat, configurable via `MCPMiddleware(history_size=50)`
- Returns error if chat not in allowlist

### `telegram://config`
- Returns current server config (no API calls)
- Fields: server_name, allowed_chat_ids, enable_broadcast, max_broadcast_recipients

## Middleware Changes

`MCPMiddleware.__init__` gains:
- `history_size: int = 50`
- `message_history: dict[int, deque[dict]]`

`MCPMiddleware.__call__` additionally:
- Extracts text messages and stores in per-chat deque
- Only text messages cached (photos/stickers skipped — no text content)

## BotContext Changes

New optional field:
- `middleware: MCPMiddleware | None = None`
- Resources check this to access cached data
- If None, chat list and history resources return empty with explanation

## Testing

- 4 resource success tests (one per resource)
- Allowlist enforcement tests for chats and history
- Middleware message caching tests (add, overflow, deque limit)
- Missing middleware graceful degradation test
- ~15-20 new tests total
