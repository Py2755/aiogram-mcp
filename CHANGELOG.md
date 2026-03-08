# Changelog

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
