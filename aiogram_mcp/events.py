"""Real-time event streaming for MCP clients."""

from __future__ import annotations

import logging
import uuid
from collections import deque
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Subscription:
    """A client's event subscription with optional filters."""

    id: str
    chat_ids: list[int] | None = None
    event_types: list[str] | None = None
    session: Any = None  # ServerSession — typed as Any for mockability


class EventManager:
    """Manage event queue and client subscriptions."""

    def __init__(self, queue_size: int = 200) -> None:
        self.queue_size = queue_size
        self._next_id: int = 1
        self._events: deque[dict[str, Any]] = deque(maxlen=queue_size)
        self._subscriptions: dict[str, Subscription] = {}

    async def push_event(self, event_data: dict[str, Any]) -> None:
        """Add an event to the queue and notify matching subscribers."""
        event = {"id": self._next_id, **event_data}
        self._next_id += 1
        self._events.append(event)
        await self._notify_subscribers(event)

    def get_events(self, since_id: int = 0) -> list[dict[str, Any]]:
        """Return events with id > since_id."""
        return [e for e in self._events if e["id"] > since_id]

    def subscribe(
        self,
        *,
        chat_ids: list[int] | None = None,
        event_types: list[str] | None = None,
        session: Any = None,
    ) -> str:
        """Create a subscription and return its ID."""
        sub_id = uuid.uuid4().hex[:12]
        self._subscriptions[sub_id] = Subscription(
            id=sub_id,
            chat_ids=chat_ids,
            event_types=event_types,
            session=session,
        )
        logger.info("Subscription %s created (chats=%s, types=%s)", sub_id, chat_ids, event_types)
        return sub_id

    def unsubscribe(self, subscription_id: str) -> bool:
        """Remove a subscription. Returns True if it existed."""
        removed = self._subscriptions.pop(subscription_id, None)
        if removed:
            logger.info("Subscription %s removed", subscription_id)
        return removed is not None

    def _matches(self, event: dict[str, Any], sub: Subscription) -> bool:
        """Check if an event matches a subscription's filters."""
        if sub.chat_ids is not None and event.get("chat_id") not in sub.chat_ids:
            return False
        return not (sub.event_types is not None and event.get("type") not in sub.event_types)

    async def _notify_subscribers(self, event: dict[str, Any]) -> None:
        """Send resource-updated notification to matching subscribers."""
        dead: list[str] = []
        for sub in self._subscriptions.values():
            if sub.session is None or not self._matches(event, sub):
                continue
            try:
                await sub.session.send_resource_updated(
                    "telegram://events/queue"
                )
            except Exception:
                logger.debug("Subscription %s session dead, removing", sub.id)
                dead.append(sub.id)
        for sub_id in dead:
            self._subscriptions.pop(sub_id, None)
