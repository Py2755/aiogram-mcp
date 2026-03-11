"""Event subscription tools: subscribe_events, unsubscribe_events."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..context import BotContext

ToolResult = dict[str, Any]


def register_event_tools(mcp: FastMCP, ctx: BotContext) -> None:
    @mcp.tool
    async def subscribe_events(
        chat_ids: list[int] | None = None,
        event_types: list[str] | None = None,
    ) -> ToolResult:
        """Subscribe to real-time Telegram events.

        Receive notifications when new events match your filters.
        Read the telegram://events/queue resource to get event data.

        Args:
            chat_ids: Only events from these chats (None = all allowed chats).
            event_types: Filter by type: "message", "command" (None = all).
        """
        if ctx.event_manager is None:
            return {
                "ok": False,
                "error": "EventManager is not configured. Pass event_manager to AiogramMCP.",
            }

        # Validate chat_ids against allowlist
        if chat_ids is not None:
            for cid in chat_ids:
                if not ctx.is_chat_allowed(cid):
                    return {
                        "ok": False,
                        "error": f"Chat {cid} is not in allowed_chat_ids.",
                    }

        sub_id = ctx.event_manager.subscribe(
            chat_ids=chat_ids,
            event_types=event_types,
        )
        return {
            "ok": True,
            "subscription_id": sub_id,
            "chat_ids": chat_ids,
            "event_types": event_types,
            "note": "Read telegram://events/queue to get events.",
        }

    @mcp.tool
    async def unsubscribe_events(subscription_id: str) -> ToolResult:
        """Unsubscribe from real-time Telegram events.

        Args:
            subscription_id: The subscription ID returned by subscribe_events.
        """
        if ctx.event_manager is None:
            return {
                "ok": False,
                "error": "EventManager is not configured.",
            }

        removed = ctx.event_manager.unsubscribe(subscription_id)
        if removed:
            return {"ok": True, "subscription_id": subscription_id}
        return {
            "ok": False,
            "error": f"Subscription '{subscription_id}' not found.",
        }
