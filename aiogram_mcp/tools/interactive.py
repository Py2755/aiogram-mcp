"""Interactive message tools: inline keyboards, message editing, callback answers."""

from __future__ import annotations

from typing import Any

from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from fastmcp import FastMCP

from ..context import BotContext

ToolResult = dict[str, Any]


def _build_keyboard(
    buttons: list[list[dict[str, str]]],
) -> InlineKeyboardMarkup | str:
    """Build InlineKeyboardMarkup from a list of button rows.

    Returns the markup on success, or an error string on validation failure.
    Each button dict must have 'text' and either 'callback_data' or 'url'.
    """
    rows: list[list[InlineKeyboardButton]] = []
    for row_idx, row in enumerate(buttons):
        built_row: list[InlineKeyboardButton] = []
        for btn_idx, btn in enumerate(row):
            if "text" not in btn:
                return f"Button [{row_idx}][{btn_idx}] is missing required 'text' field."
            if "callback_data" not in btn and "url" not in btn:
                return (
                    f"Button [{row_idx}][{btn_idx}] must have 'callback_data' or 'url'."
                )
            built_row.append(
                InlineKeyboardButton(
                    text=btn["text"],
                    callback_data=btn.get("callback_data"),
                    url=btn.get("url"),
                )
            )
        rows.append(built_row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _normalize_parse_mode(parse_mode: str | None) -> ParseMode | None:
    if parse_mode is None:
        return None
    normalized = parse_mode.strip().upper()
    if normalized == "HTML":
        return ParseMode.HTML
    if normalized in {"MARKDOWN", "MARKDOWNV2"}:
        return ParseMode.MARKDOWN_V2
    raise ValueError("parse_mode must be one of: HTML, Markdown, MarkdownV2, or None")


def register_interactive_tools(mcp: FastMCP, ctx: BotContext) -> None:
    @mcp.tool
    async def send_interactive_message(
        chat_id: int,
        text: str,
        buttons: list[list[dict[str, str]]],
        parse_mode: str | None = "HTML",
        disable_notification: bool = False,
    ) -> ToolResult:
        """Send a message with inline keyboard buttons.

        Args:
            chat_id: Target chat ID.
            text: Message text.
            buttons: Rows of buttons. Each button: {"text": "Label", "callback_data": "value"}
                     or {"text": "Label", "url": "https://..."}.
            parse_mode: HTML, Markdown, MarkdownV2, or None.
            disable_notification: Send silently.
        """
        if not ctx.is_chat_allowed(chat_id):
            return {
                "ok": False,
                "error": f"Chat {chat_id} is not in allowed_chat_ids.",
            }

        keyboard = _build_keyboard(buttons)
        if isinstance(keyboard, str):
            return {"ok": False, "error": keyboard}

        try:
            msg = await ctx.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=_normalize_parse_mode(parse_mode),
                reply_markup=keyboard,
                disable_notification=disable_notification,
            )
            return {
                "ok": True,
                "message_id": msg.message_id,
                "chat_id": msg.chat.id,
                "date": msg.date.isoformat(),
            }
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        except (TelegramBadRequest, TelegramForbiddenError) as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool
    async def edit_message(
        chat_id: int,
        message_id: int,
        text: str,
        buttons: list[list[dict[str, str]]] | None = None,
        parse_mode: str | None = "HTML",
    ) -> ToolResult:
        """Edit the text and/or inline keyboard of an existing message.

        Args:
            chat_id: Chat containing the message.
            message_id: ID of the message to edit.
            text: New message text.
            buttons: New inline keyboard (None to remove buttons).
            parse_mode: HTML, Markdown, MarkdownV2, or None.
        """
        if not ctx.is_chat_allowed(chat_id):
            return {
                "ok": False,
                "error": f"Chat {chat_id} is not in allowed_chat_ids.",
            }

        reply_markup = None
        if buttons is not None:
            keyboard = _build_keyboard(buttons)
            if isinstance(keyboard, str):
                return {"ok": False, "error": keyboard}
            reply_markup = keyboard

        try:
            result = await ctx.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                parse_mode=_normalize_parse_mode(parse_mode),
                reply_markup=reply_markup,
            )
            if isinstance(result, bool):
                return {"ok": True, "message_id": message_id, "chat_id": chat_id}
            return {
                "ok": True,
                "message_id": result.message_id,
                "chat_id": result.chat.id,
            }
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        except (TelegramBadRequest, TelegramForbiddenError) as exc:
            return {"ok": False, "error": str(exc)}

    @mcp.tool
    async def answer_callback_query(
        callback_query_id: str,
        text: str | None = None,
        show_alert: bool = False,
    ) -> ToolResult:
        """Answer a callback query from an inline keyboard button press.

        Args:
            callback_query_id: ID of the callback query (from the event).
            text: Optional notification text shown to the user.
            show_alert: Show as alert popup instead of toast notification.
        """
        try:
            await ctx.bot.answer_callback_query(
                callback_query_id=callback_query_id,
                text=text,
                show_alert=show_alert,
            )
            return {"ok": True, "callback_query_id": callback_query_id}
        except (TelegramBadRequest, TelegramForbiddenError) as exc:
            return {"ok": False, "error": str(exc)}
