# Changelog

## 0.7.1 (2026-03-14)

### Added
- Dockerfile for containerized deployment and Glama listing
- `server.json` for MCP Registry listing
- MCP Registry badge in README

## 0.7.0 (2026-03-14)

### Added
- Token bucket rate limiter — limits outgoing Telegram API calls to configurable requests/sec
- Permission levels (read, messaging, moderation, admin) — control which tools AI agents can access
- Audit log with MCP resource `telegram://audit/log` — track all tool invocations
- `RateLimiter` class in `aiogram_mcp/rate_limiter.py`
- `PermissionLevel` enum and helpers in `aiogram_mcp/permissions.py`
- `AuditLogger` and `AuditEntry` in `aiogram_mcp/audit.py`

### Changed
- `AiogramMCP` accepts new parameters: `permission_level`, `rate_limit`, `enable_audit`, `audit_log_size`
- `BotContext` extended with `rate_limiter` and `audit_logger` fields
- `telegram://config` resource now includes permission_level, rate_limit, audit settings
- All `register_*_tools()` functions accept `allowed_tools` parameter for permission filtering
- Broadcast tool uses rate limiter instead of fixed `delay_seconds` sleep when rate limiter is active

## 0.6.0 (2026-03-12)

### Added
- Pydantic result models with `outputSchema` for all existing tools — AI clients can parse responses programmatically via `structuredContent`
- 10 rich media tools: `send_document`, `send_voice`, `send_video`, `send_animation`, `send_audio`, `send_sticker`, `send_video_note`, `send_contact`, `send_location`, `send_poll`
- File metadata resource `telegram://files/{file_id}` — retrieve file info without downloading
- Base `ToolResponse` and `OkResult` models in `aiogram_mcp/models.py`
- Shared `normalize_parse_mode` utility in `aiogram_mcp/utils.py`

### Changed
- All tool return types changed from `dict[str, Any]` to typed Pydantic models
- `_normalize_parse_mode` moved from `tools/messaging.py` to `aiogram_mcp/utils.py` and renamed to `normalize_parse_mode`

### Removed
- `ToolResult` type alias removed from all tool modules

## 0.5.0 (2026-03-12)

### Added
- Interactive messages with inline keyboard buttons (Phase 4)
- `send_interactive_message` tool — send messages with inline keyboard (callback buttons + URL buttons)
- `edit_message` tool — edit text and/or inline keyboard of existing messages
- `answer_callback_query` tool — respond to inline button presses
- `MCPMiddleware` now detects callback queries and pushes `callback_query` events to EventManager
- Button validation: checks for required `text` field and `callback_data` or `url` action
- Register middleware on `dp.callback_query` to enable callback tracking

## 0.4.0 (2026-03-11)

### Added
- Real-time event streaming (Phase 3)
- `EventManager` class for managing event queues and client subscriptions
- `subscribe_events` tool — subscribe to Telegram events with chat/type filters
- `unsubscribe_events` tool — remove event subscriptions
- `telegram://events/queue` resource — read queued events with auto-incrementing IDs
- `MCPMiddleware` now pushes events to `EventManager` (message and command types)
- Push notifications via MCP `notifications/resources/updated` for subscribed clients
- Dead session cleanup — disconnected subscribers are automatically removed

## 0.3.0 (2026-03-08)

### Added
- 3 MCP Prompts: `moderation_prompt`, `announcement_prompt`, `user_report_prompt`
- Prompts give AI agents ready-made workflows instead of raw tools
- `moderation_prompt` — review user behavior with message history and suggest action
- `announcement_prompt` — draft Telegram announcements with formatting guidelines
- `user_report_prompt` — compile comprehensive user activity reports

## 0.2.0 (2026-03-07)

### Added
- 4 MCP Resources: `telegram://bot/info`, `telegram://config`, `telegram://chats`, `telegram://chats/{chat_id}/history`
- `MCPMiddleware` now caches message history per chat (configurable `history_size`)
- `BotContext` accepts optional `middleware` parameter
- `AiogramMCP` accepts optional `middleware` parameter to enable resource tracking

## 0.1.0

- Initial public package structure.
- Added MCP server core, middleware, tool registry, tests, and examples.
- Added GitHub workflows, issue templates, PR template, and release docs.
- Replaced the private-domain example with a generic incident alerting example.
