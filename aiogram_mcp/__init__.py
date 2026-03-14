"""Public package exports for aiogram-mcp."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .audit import AuditLogger
from .context import BotContext
from .events import EventManager
from .middleware import MCPMiddleware
from .permissions import PermissionLevel
from .rate_limiter import RateLimiter
from .server import AiogramMCP

try:
    __version__ = version("aiogram-mcp")
except PackageNotFoundError:
    __version__ = "0.7.1"

__all__ = [
    "AiogramMCP",
    "AuditLogger",
    "BotContext",
    "EventManager",
    "MCPMiddleware",
    "PermissionLevel",
    "RateLimiter",
    "__version__",
]
