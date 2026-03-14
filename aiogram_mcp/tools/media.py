"""Rich media tools: document, voice, video, animation, audio, sticker, video_note, contact, location, poll."""

from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import InputPollOption
from fastmcp import FastMCP

from ..context import BotContext
from ..models import ToolResponse
from ..utils import normalize_parse_mode


class SendMediaResult(ToolResponse):
    message_id: int | None = None
    chat_id: int | None = None


class SendPollResult(ToolResponse):
    message_id: int | None = None
    chat_id: int | None = None
    poll_id: str | None = None


def register_media_tools(
    mcp: FastMCP, ctx: BotContext, allowed_tools: set[str] | None = None
) -> None:
    if allowed_tools is None or "send_document" in allowed_tools:

        @mcp.tool
        async def send_document(
            chat_id: int,
            document_url: str,
            caption: str | None = None,
            parse_mode: str | None = "HTML",
            disable_notification: bool = False,
        ) -> SendMediaResult:
            """Send a document/file to a Telegram chat.

            Args:
                chat_id: Target chat ID.
                document_url: URL or file_id of the document.
                caption: Optional caption.
                parse_mode: HTML, Markdown, MarkdownV2, or None.
                disable_notification: Send silently.
            """
            if not ctx.is_chat_allowed(chat_id):
                return SendMediaResult(ok=False, error=f"Chat {chat_id} is not allowed.")
            try:
                msg = await ctx.bot.send_document(
                    chat_id=chat_id,
                    document=document_url,
                    caption=caption,
                    parse_mode=normalize_parse_mode(parse_mode),
                    disable_notification=disable_notification,
                )
                return SendMediaResult(ok=True, message_id=msg.message_id, chat_id=msg.chat.id)
            except ValueError as exc:
                return SendMediaResult(ok=False, error=str(exc))
            except (TelegramBadRequest, TelegramForbiddenError) as exc:
                return SendMediaResult(ok=False, error=str(exc))

    if allowed_tools is None or "send_voice" in allowed_tools:

        @mcp.tool
        async def send_voice(
            chat_id: int,
            voice_url: str,
            caption: str | None = None,
            parse_mode: str | None = "HTML",
            duration: int | None = None,
            disable_notification: bool = False,
        ) -> SendMediaResult:
            """Send a voice message to a Telegram chat.

            Args:
                chat_id: Target chat ID.
                voice_url: URL or file_id of the voice message (OGG with OPUS).
                caption: Optional caption.
                parse_mode: HTML, Markdown, MarkdownV2, or None.
                duration: Duration in seconds.
                disable_notification: Send silently.
            """
            if not ctx.is_chat_allowed(chat_id):
                return SendMediaResult(ok=False, error=f"Chat {chat_id} is not allowed.")
            try:
                msg = await ctx.bot.send_voice(
                    chat_id=chat_id,
                    voice=voice_url,
                    caption=caption,
                    parse_mode=normalize_parse_mode(parse_mode),
                    duration=duration,
                    disable_notification=disable_notification,
                )
                return SendMediaResult(ok=True, message_id=msg.message_id, chat_id=msg.chat.id)
            except ValueError as exc:
                return SendMediaResult(ok=False, error=str(exc))
            except (TelegramBadRequest, TelegramForbiddenError) as exc:
                return SendMediaResult(ok=False, error=str(exc))

    if allowed_tools is None or "send_video" in allowed_tools:

        @mcp.tool
        async def send_video(
            chat_id: int,
            video_url: str,
            caption: str | None = None,
            parse_mode: str | None = "HTML",
            duration: int | None = None,
            disable_notification: bool = False,
        ) -> SendMediaResult:
            """Send a video to a Telegram chat.

            Args:
                chat_id: Target chat ID.
                video_url: URL or file_id of the video.
                caption: Optional caption.
                parse_mode: HTML, Markdown, MarkdownV2, or None.
                duration: Duration in seconds.
                disable_notification: Send silently.
            """
            if not ctx.is_chat_allowed(chat_id):
                return SendMediaResult(ok=False, error=f"Chat {chat_id} is not allowed.")
            try:
                msg = await ctx.bot.send_video(
                    chat_id=chat_id,
                    video=video_url,
                    caption=caption,
                    parse_mode=normalize_parse_mode(parse_mode),
                    duration=duration,
                    disable_notification=disable_notification,
                )
                return SendMediaResult(ok=True, message_id=msg.message_id, chat_id=msg.chat.id)
            except ValueError as exc:
                return SendMediaResult(ok=False, error=str(exc))
            except (TelegramBadRequest, TelegramForbiddenError) as exc:
                return SendMediaResult(ok=False, error=str(exc))

    if allowed_tools is None or "send_animation" in allowed_tools:

        @mcp.tool
        async def send_animation(
            chat_id: int,
            animation_url: str,
            caption: str | None = None,
            parse_mode: str | None = "HTML",
            disable_notification: bool = False,
        ) -> SendMediaResult:
            """Send a GIF/animation to a Telegram chat.

            Args:
                chat_id: Target chat ID.
                animation_url: URL or file_id of the animation.
                caption: Optional caption.
                parse_mode: HTML, Markdown, MarkdownV2, or None.
                disable_notification: Send silently.
            """
            if not ctx.is_chat_allowed(chat_id):
                return SendMediaResult(ok=False, error=f"Chat {chat_id} is not allowed.")
            try:
                msg = await ctx.bot.send_animation(
                    chat_id=chat_id,
                    animation=animation_url,
                    caption=caption,
                    parse_mode=normalize_parse_mode(parse_mode),
                    disable_notification=disable_notification,
                )
                return SendMediaResult(ok=True, message_id=msg.message_id, chat_id=msg.chat.id)
            except ValueError as exc:
                return SendMediaResult(ok=False, error=str(exc))
            except (TelegramBadRequest, TelegramForbiddenError) as exc:
                return SendMediaResult(ok=False, error=str(exc))

    if allowed_tools is None or "send_audio" in allowed_tools:

        @mcp.tool
        async def send_audio(
            chat_id: int,
            audio_url: str,
            caption: str | None = None,
            parse_mode: str | None = "HTML",
            performer: str | None = None,
            title: str | None = None,
            disable_notification: bool = False,
        ) -> SendMediaResult:
            """Send an audio file (music) to a Telegram chat.

            Args:
                chat_id: Target chat ID.
                audio_url: URL or file_id of the audio (MP3/M4A).
                caption: Optional caption.
                parse_mode: HTML, Markdown, MarkdownV2, or None.
                performer: Performer name.
                title: Track title.
                disable_notification: Send silently.
            """
            if not ctx.is_chat_allowed(chat_id):
                return SendMediaResult(ok=False, error=f"Chat {chat_id} is not allowed.")
            try:
                msg = await ctx.bot.send_audio(
                    chat_id=chat_id,
                    audio=audio_url,
                    caption=caption,
                    parse_mode=normalize_parse_mode(parse_mode),
                    performer=performer,
                    title=title,
                    disable_notification=disable_notification,
                )
                return SendMediaResult(ok=True, message_id=msg.message_id, chat_id=msg.chat.id)
            except ValueError as exc:
                return SendMediaResult(ok=False, error=str(exc))
            except (TelegramBadRequest, TelegramForbiddenError) as exc:
                return SendMediaResult(ok=False, error=str(exc))

    if allowed_tools is None or "send_sticker" in allowed_tools:

        @mcp.tool
        async def send_sticker(
            chat_id: int,
            sticker: str,
            disable_notification: bool = False,
        ) -> SendMediaResult:
            """Send a sticker to a Telegram chat.

            Args:
                chat_id: Target chat ID.
                sticker: File ID or URL of the sticker (WEBP/TGS/WEBM).
                disable_notification: Send silently.
            """
            if not ctx.is_chat_allowed(chat_id):
                return SendMediaResult(ok=False, error=f"Chat {chat_id} is not allowed.")
            try:
                msg = await ctx.bot.send_sticker(
                    chat_id=chat_id,
                    sticker=sticker,
                    disable_notification=disable_notification,
                )
                return SendMediaResult(ok=True, message_id=msg.message_id, chat_id=msg.chat.id)
            except (TelegramBadRequest, TelegramForbiddenError) as exc:
                return SendMediaResult(ok=False, error=str(exc))

    if allowed_tools is None or "send_video_note" in allowed_tools:

        @mcp.tool
        async def send_video_note(
            chat_id: int,
            video_note_url: str,
            duration: int | None = None,
            length: int | None = None,
            disable_notification: bool = False,
        ) -> SendMediaResult:
            """Send a video note (round video) to a Telegram chat.

            Args:
                chat_id: Target chat ID.
                video_note_url: URL or file_id of the video note.
                duration: Duration in seconds.
                length: Video width and height (diameter of the circle).
                disable_notification: Send silently.
            """
            if not ctx.is_chat_allowed(chat_id):
                return SendMediaResult(ok=False, error=f"Chat {chat_id} is not allowed.")
            try:
                msg = await ctx.bot.send_video_note(
                    chat_id=chat_id,
                    video_note=video_note_url,
                    duration=duration,
                    length=length,
                    disable_notification=disable_notification,
                )
                return SendMediaResult(ok=True, message_id=msg.message_id, chat_id=msg.chat.id)
            except (TelegramBadRequest, TelegramForbiddenError) as exc:
                return SendMediaResult(ok=False, error=str(exc))

    if allowed_tools is None or "send_contact" in allowed_tools:

        @mcp.tool
        async def send_contact(
            chat_id: int,
            phone_number: str,
            first_name: str,
            last_name: str | None = None,
            disable_notification: bool = False,
        ) -> SendMediaResult:
            """Send a phone contact to a Telegram chat.

            Args:
                chat_id: Target chat ID.
                phone_number: Contact's phone number.
                first_name: Contact's first name.
                last_name: Contact's last name.
                disable_notification: Send silently.
            """
            if not ctx.is_chat_allowed(chat_id):
                return SendMediaResult(ok=False, error=f"Chat {chat_id} is not allowed.")
            try:
                msg = await ctx.bot.send_contact(
                    chat_id=chat_id,
                    phone_number=phone_number,
                    first_name=first_name,
                    last_name=last_name,
                    disable_notification=disable_notification,
                )
                return SendMediaResult(ok=True, message_id=msg.message_id, chat_id=msg.chat.id)
            except (TelegramBadRequest, TelegramForbiddenError) as exc:
                return SendMediaResult(ok=False, error=str(exc))

    if allowed_tools is None or "send_location" in allowed_tools:

        @mcp.tool
        async def send_location(
            chat_id: int,
            latitude: float,
            longitude: float,
            disable_notification: bool = False,
        ) -> SendMediaResult:
            """Send a location to a Telegram chat.

            Args:
                chat_id: Target chat ID.
                latitude: Latitude of the location.
                longitude: Longitude of the location.
                disable_notification: Send silently.
            """
            if not ctx.is_chat_allowed(chat_id):
                return SendMediaResult(ok=False, error=f"Chat {chat_id} is not allowed.")
            try:
                msg = await ctx.bot.send_location(
                    chat_id=chat_id,
                    latitude=latitude,
                    longitude=longitude,
                    disable_notification=disable_notification,
                )
                return SendMediaResult(ok=True, message_id=msg.message_id, chat_id=msg.chat.id)
            except (TelegramBadRequest, TelegramForbiddenError) as exc:
                return SendMediaResult(ok=False, error=str(exc))

    if allowed_tools is None or "send_poll" in allowed_tools:

        @mcp.tool
        async def send_poll(
            chat_id: int,
            question: str,
            options: list[str],
            is_anonymous: bool = True,
            type: str = "regular",
            allows_multiple_answers: bool = False,
            disable_notification: bool = False,
        ) -> SendPollResult:
            """Send a poll to a Telegram chat.

            Args:
                chat_id: Target chat ID.
                question: Poll question (1-300 characters).
                options: List of answer options (2-10 strings).
                is_anonymous: Whether the poll is anonymous.
                type: "regular" or "quiz".
                allows_multiple_answers: Allow multiple answers (regular polls only).
                disable_notification: Send silently.
            """
            if not ctx.is_chat_allowed(chat_id):
                return SendPollResult(ok=False, error=f"Chat {chat_id} is not allowed.")
            try:
                poll_options: list[InputPollOption | str] = [InputPollOption(text=opt) for opt in options]
                msg = await ctx.bot.send_poll(
                    chat_id=chat_id,
                    question=question,
                    options=poll_options,
                    is_anonymous=is_anonymous,
                    type=type,
                    allows_multiple_answers=allows_multiple_answers,
                    disable_notification=disable_notification,
                )
                return SendPollResult(
                    ok=True,
                    message_id=msg.message_id,
                    chat_id=msg.chat.id,
                    poll_id=msg.poll.id if msg.poll else None,
                )
            except (TelegramBadRequest, TelegramForbiddenError) as exc:
                return SendPollResult(ok=False, error=str(exc))
