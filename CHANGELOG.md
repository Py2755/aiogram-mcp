# Changelog

## 0.2.0 (unreleased)

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
