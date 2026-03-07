"""Public package exports for aiogram-mcp."""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .context import BotContext
from .middleware import MCPMiddleware
from .server import AiogramMCP

try:
    __version__ = version("aiogram-mcp")
except PackageNotFoundError:
    __version__ = "0.2.0"

__all__ = ["AiogramMCP", "BotContext", "MCPMiddleware", "__version__"]
