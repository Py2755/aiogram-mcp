"""Interactive message tools: inline keyboards, message editing, callback answers."""

from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from fastmcp import FastMCP

from ..context import BotContext
from ..models import ToolResponse
from ..utils import normalize_parse_mode


class SendInteractiveResult(ToolResponse):
    message_id: int | None = None
    chat_id: int | None = None
    date: str | None = None


class EditMessageResult(ToolResponse):
    message_id: int | None = None
    chat_id: int | None = None


class AnswerCallbackResult(ToolResponse):
    callback_query_id: str | None = None


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


def register_interactive_tools(
    mcp: FastMCP, ctx: BotContext, allowed_tools: set[str] | None = None
) -> None:
    if allowed_tools is None or "send_interactive_message" in allowed_tools:

        @mcp.tool
        async def send_interactive_message(
            chat_id: int,
            text: str,
            buttons: list[list[dict[str, str]]],
            parse_mode: str | None = "HTML",
            disable_notification: bool = False,
        ) -> SendInteractiveResult:
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
                result = SendInteractiveResult(
                    ok=False,
                    error=f"Chat {chat_id} is not in allowed_chat_ids.",
                )
                if ctx.audit_logger:
                    ctx.audit_logger.log(
                        "send_interactive_message",
                        {"chat_id": chat_id, "text": text},
                        result.ok,
                        result.error,
                    )
                return result

            keyboard = _build_keyboard(buttons)
            if isinstance(keyboard, str):
                result = SendInteractiveResult(ok=False, error=keyboard)
                if ctx.audit_logger:
                    ctx.audit_logger.log(
                        "send_interactive_message",
                        {"chat_id": chat_id, "text": text},
                        result.ok,
                        result.error,
                    )
                return result

            try:
                if ctx.rate_limiter:
                    await ctx.rate_limiter.acquire()
                msg = await ctx.bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    parse_mode=normalize_parse_mode(parse_mode),
                    reply_markup=keyboard,
                    disable_notification=disable_notification,
                )
                result = SendInteractiveResult(
                    ok=True,
                    message_id=msg.message_id,
                    chat_id=msg.chat.id,
                    date=msg.date.isoformat(),
                )
            except ValueError as exc:
                result = SendInteractiveResult(ok=False, error=str(exc))
            except (TelegramBadRequest, TelegramForbiddenError) as exc:
                result = SendInteractiveResult(ok=False, error=str(exc))

            if ctx.audit_logger:
                ctx.audit_logger.log(
                    "send_interactive_message",
                    {"chat_id": chat_id, "text": text},
                    result.ok,
                    result.error,
                )
            return result

    if allowed_tools is None or "edit_message" in allowed_tools:

        @mcp.tool
        async def edit_message(
            chat_id: int,
            message_id: int,
            text: str,
            buttons: list[list[dict[str, str]]] | None = None,
            parse_mode: str | None = "HTML",
        ) -> EditMessageResult:
            """Edit the text and/or inline keyboard of an existing message.

            Args:
                chat_id: Chat containing the message.
                message_id: ID of the message to edit.
                text: New message text.
                buttons: New inline keyboard (None to remove buttons).
                parse_mode: HTML, Markdown, MarkdownV2, or None.
            """
            if not ctx.is_chat_allowed(chat_id):
                result = EditMessageResult(
                    ok=False,
                    error=f"Chat {chat_id} is not in allowed_chat_ids.",
                )
                if ctx.audit_logger:
                    ctx.audit_logger.log(
                        "edit_message",
                        {"chat_id": chat_id, "message_id": message_id, "text": text},
                        result.ok,
                        result.error,
                    )
                return result

            reply_markup = None
            if buttons is not None:
                keyboard = _build_keyboard(buttons)
                if isinstance(keyboard, str):
                    result = EditMessageResult(ok=False, error=keyboard)
                    if ctx.audit_logger:
                        ctx.audit_logger.log(
                            "edit_message",
                            {"chat_id": chat_id, "message_id": message_id, "text": text},
                            result.ok,
                            result.error,
                        )
                    return result
                reply_markup = keyboard

            try:
                if ctx.rate_limiter:
                    await ctx.rate_limiter.acquire()
                api_result = await ctx.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text,
                    parse_mode=normalize_parse_mode(parse_mode),
                    reply_markup=reply_markup,
                )
                if isinstance(api_result, bool):
                    result = EditMessageResult(ok=True, message_id=message_id, chat_id=chat_id)
                else:
                    result = EditMessageResult(
                        ok=True,
                        message_id=api_result.message_id,
                        chat_id=api_result.chat.id,
                    )
            except ValueError as exc:
                result = EditMessageResult(ok=False, error=str(exc))
            except (TelegramBadRequest, TelegramForbiddenError) as exc:
                result = EditMessageResult(ok=False, error=str(exc))

            if ctx.audit_logger:
                ctx.audit_logger.log(
                    "edit_message",
                    {"chat_id": chat_id, "message_id": message_id, "text": text},
                    result.ok,
                    result.error,
                )
            return result

    if allowed_tools is None or "answer_callback_query" in allowed_tools:

        @mcp.tool
        async def answer_callback_query(
            callback_query_id: str,
            text: str | None = None,
            show_alert: bool = False,
        ) -> AnswerCallbackResult:
            """Answer a callback query from an inline keyboard button press.

            Args:
                callback_query_id: ID of the callback query (from the event).
                text: Optional notification text shown to the user.
                show_alert: Show as alert popup instead of toast notification.
            """
            try:
                if ctx.rate_limiter:
                    await ctx.rate_limiter.acquire()
                await ctx.bot.answer_callback_query(
                    callback_query_id=callback_query_id,
                    text=text,
                    show_alert=show_alert,
                )
                result = AnswerCallbackResult(ok=True, callback_query_id=callback_query_id)
            except (TelegramBadRequest, TelegramForbiddenError) as exc:
                result = AnswerCallbackResult(ok=False, error=str(exc))

            if ctx.audit_logger:
                ctx.audit_logger.log(
                    "answer_callback_query",
                    {"callback_query_id": callback_query_id},
                    result.ok,
                    result.error,
                )
            return result
