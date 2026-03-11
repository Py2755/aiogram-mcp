"""Tests for aiogram-mcp."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from aiogram_mcp.context import BotContext
from aiogram_mcp.events import EventManager, Subscription
from aiogram_mcp.middleware import MCPMiddleware
from aiogram_mcp.server import AiogramMCP


def get_tool_names(fast_mcp) -> list[str]:
    tools = asyncio.run(fast_mcp.list_tools())
    return [tool.name for tool in tools]


async def get_tool_map(fast_mcp):
    tools = await fast_mcp.list_tools()
    return {tool.name: tool for tool in tools}


def _make_fast_mcp():
    from fastmcp import FastMCP

    return FastMCP("test")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_bot():
    bot = AsyncMock()
    bot.get_me = AsyncMock(
        return_value=MagicMock(
            id=123456789,
            username="test_bot",
            first_name="Test Bot",
            is_bot=True,
            can_join_groups=True,
            can_read_all_group_messages=False,
            supports_inline_queries=False,
        )
    )
    bot.send_message = AsyncMock(
        return_value=MagicMock(
            message_id=42,
            chat=MagicMock(id=111),
            date=MagicMock(isoformat=lambda: "2026-03-07T12:00:00"),
        )
    )
    bot.send_photo = AsyncMock(
        return_value=MagicMock(
            message_id=43,
            chat=MagicMock(id=111),
        )
    )
    bot.forward_message = AsyncMock(
        return_value=MagicMock(message_id=44)
    )
    bot.delete_message = AsyncMock(return_value=True)
    bot.pin_chat_message = AsyncMock(return_value=True)
    bot.get_chat = AsyncMock(
        return_value=MagicMock(
            id=-1001234,
            type=MagicMock(value="supergroup"),
            title="Test Group",
            username="testgroup",
            description="A test group",
            is_forum=False,
        )
    )
    bot.get_chat_member_count = AsyncMock(return_value=42)
    bot.get_chat_member = AsyncMock(
        return_value=MagicMock(
            user=MagicMock(
                id=555,
                username="testuser",
                first_name="Test",
                last_name="User",
                language_code="en",
                is_bot=False,
                is_premium=None,
            ),
            status=MagicMock(value="member"),
        )
    )
    bot.get_user_profile_photos = AsyncMock(
        return_value=MagicMock(
            total_count=1,
            photos=[
                [
                    MagicMock(
                        file_id="photo_id_1",
                        file_unique_id="unique_1",
                        width=320,
                        height=320,
                        file_size=12345,
                    )
                ]
            ],
        )
    )
    bot.ban_chat_member = AsyncMock(return_value=True)
    bot.unban_chat_member = AsyncMock(return_value=True)
    bot.set_chat_title = AsyncMock(return_value=True)
    bot.set_chat_description = AsyncMock(return_value=True)
    bot.session = MagicMock(close=AsyncMock())
    return bot


@pytest.fixture
def mock_dp():
    dispatcher = MagicMock()
    dispatcher.start_polling = AsyncMock()
    return dispatcher


@pytest.fixture
def ctx(mock_bot, mock_dp):
    return BotContext(bot=mock_bot, dp=mock_dp)


@pytest.fixture
def ctx_with_allowlist(mock_bot, mock_dp):
    return BotContext(bot=mock_bot, dp=mock_dp, allowed_chat_ids=[111, 222])


# ---------------------------------------------------------------------------
# BotContext
# ---------------------------------------------------------------------------


class TestBotContext:
    def test_all_chats_allowed_by_default(self, ctx):
        assert ctx.is_chat_allowed(999999) is True

    def test_allowlist_permits_listed_chat(self, ctx_with_allowlist):
        assert ctx_with_allowlist.is_chat_allowed(111) is True

    def test_allowlist_blocks_unlisted_chat(self, ctx_with_allowlist):
        assert ctx_with_allowlist.is_chat_allowed(999) is False

    def test_empty_allowlist_blocks_all(self, mock_bot, mock_dp):
        ctx = BotContext(bot=mock_bot, dp=mock_dp, allowed_chat_ids=[])
        assert ctx.is_chat_allowed(111) is False

    def test_middleware_default_none(self, ctx):
        assert ctx.middleware is None

    def test_middleware_assigned(self, mock_bot, mock_dp):
        mw = MCPMiddleware()
        ctx = BotContext(bot=mock_bot, dp=mock_dp, middleware=mw)
        assert ctx.middleware is mw


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


class TestMiddleware:
    @pytest.mark.asyncio
    async def test_tracks_active_chat_and_user(self):
        middleware = MCPMiddleware()
        event = MagicMock(
            chat=MagicMock(id=111),
            from_user=MagicMock(id=222),
        )
        handler = AsyncMock(return_value="ok")

        result = await middleware(handler, event, {})

        assert result == "ok"
        assert middleware.active_chat_ids == {111}
        assert middleware.active_user_ids == {222}

    @pytest.mark.asyncio
    async def test_handles_event_without_chat(self):
        middleware = MCPMiddleware()
        event = MagicMock(spec=[])  # no chat, no from_user attributes
        handler = AsyncMock(return_value="ok")

        result = await middleware(handler, event, {})

        assert result == "ok"
        assert middleware.active_chat_ids == set()
        assert middleware.active_user_ids == set()

    @pytest.mark.asyncio
    async def test_tracks_multiple_events(self):
        middleware = MCPMiddleware()
        handler = AsyncMock(return_value="ok")

        for chat_id, user_id in [(111, 1), (222, 2), (111, 3)]:
            event = MagicMock(
                chat=MagicMock(id=chat_id),
                from_user=MagicMock(id=user_id),
            )
            await middleware(handler, event, {})

        assert middleware.active_chat_ids == {111, 222}
        assert middleware.active_user_ids == {1, 2, 3}


class TestMiddlewareHistory:
    @pytest.mark.asyncio
    async def test_caches_text_message(self):
        middleware = MCPMiddleware(history_size=50)
        event = MagicMock(
            chat=MagicMock(id=111),
            from_user=MagicMock(id=222, username="alice"),
            text="Hello world",
            message_id=1,
            date=MagicMock(isoformat=lambda: "2026-03-07T12:00:00"),
        )
        handler = AsyncMock(return_value="ok")
        await middleware(handler, event, {})

        assert len(middleware.message_history[111]) == 1
        msg = middleware.message_history[111][0]
        assert msg["text"] == "Hello world"
        assert msg["from_user_id"] == 222

    @pytest.mark.asyncio
    async def test_skips_non_text_message(self):
        middleware = MCPMiddleware(history_size=50)
        event = MagicMock(
            chat=MagicMock(id=111),
            from_user=MagicMock(id=222, username="alice"),
            text=None,
            message_id=1,
            date=MagicMock(isoformat=lambda: "2026-03-07T12:00:00"),
        )
        handler = AsyncMock(return_value="ok")
        await middleware(handler, event, {})

        assert len(middleware.message_history.get(111, [])) == 0

    @pytest.mark.asyncio
    async def test_respects_history_size_limit(self):
        middleware = MCPMiddleware(history_size=3)
        handler = AsyncMock(return_value="ok")

        for i in range(5):
            event = MagicMock(
                chat=MagicMock(id=111),
                from_user=MagicMock(id=222, username="alice"),
                text=f"Message {i}",
                message_id=i,
                date=MagicMock(isoformat=lambda: "2026-03-07T12:00:00"),
            )
            await middleware(handler, event, {})

        assert len(middleware.message_history[111]) == 3
        assert middleware.message_history[111][0]["text"] == "Message 2"

    @pytest.mark.asyncio
    async def test_default_history_size(self):
        middleware = MCPMiddleware()
        assert middleware.history_size == 50


# ---------------------------------------------------------------------------
# AiogramMCP init
# ---------------------------------------------------------------------------


class TestAiogramMCPInit:
    def test_creates_without_error(self, mock_bot, mock_dp):
        mcp = AiogramMCP(bot=mock_bot, dp=mock_dp)
        assert mcp is not None

    def test_broadcast_disabled_by_default(self, mock_bot, mock_dp):
        mcp = AiogramMCP(bot=mock_bot, dp=mock_dp)
        tool_names = get_tool_names(mcp.fastmcp)
        assert "broadcast" not in tool_names

    def test_broadcast_enabled_when_requested(self, mock_bot, mock_dp):
        mcp = AiogramMCP(bot=mock_bot, dp=mock_dp, enable_broadcast=True)
        tool_names = get_tool_names(mcp.fastmcp)
        assert "broadcast" in tool_names

    def test_core_tools_registered(self, mock_bot, mock_dp):
        mcp = AiogramMCP(bot=mock_bot, dp=mock_dp)
        tool_names = get_tool_names(mcp.fastmcp)
        expected = [
            "send_message",
            "send_photo",
            "forward_message",
            "delete_message",
            "pin_message",
            "get_bot_info",
            "get_chat_member_info",
            "get_user_profile_photos",
            "get_chat_info",
            "get_chat_members_count",
            "ban_user",
            "unban_user",
            "set_chat_title",
            "set_chat_description",
        ]
        for name in expected:
            assert name in tool_names, f"Tool '{name}' not registered"

    def test_invalid_transport_raises(self, mock_bot, mock_dp):
        mcp = AiogramMCP(bot=mock_bot, dp=mock_dp)

        with pytest.raises(ValueError):
            asyncio.run(mcp.run_alongside_bot(transport="invalid"))

    def test_custom_name(self, mock_bot, mock_dp):
        mcp = AiogramMCP(bot=mock_bot, dp=mock_dp, name="my-bot")
        assert mcp.name == "my-bot"

    def test_fastmcp_property(self, mock_bot, mock_dp):
        from fastmcp import FastMCP

        mcp = AiogramMCP(bot=mock_bot, dp=mock_dp)
        assert isinstance(mcp.fastmcp, FastMCP)

    def test_resources_registered(self, mock_bot, mock_dp):
        mcp = AiogramMCP(bot=mock_bot, dp=mock_dp)
        resources = asyncio.run(mcp.fastmcp.list_resources())
        uris = [str(r.uri) for r in resources]
        assert "telegram://bot/info" in uris
        assert "telegram://config" in uris
        assert "telegram://chats" in uris

    def test_middleware_passed_to_context(self, mock_bot, mock_dp):
        mw = MCPMiddleware()
        mcp = AiogramMCP(bot=mock_bot, dp=mock_dp, middleware=mw)
        assert mcp._ctx.middleware is mw


# ---------------------------------------------------------------------------
# Messaging tools
# ---------------------------------------------------------------------------


class TestSendMessage:
    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.messaging import register_messaging_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_messaging_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["send_message"].fn(chat_id=111, text="Hello test")
        assert result["ok"] is True
        assert result["message_id"] == 42

    @pytest.mark.asyncio
    async def test_send_message_blocked_by_allowlist(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.messaging import register_messaging_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp, allowed_chat_ids=[111])
        register_messaging_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["send_message"].fn(chat_id=999, text="Should be blocked")
        assert result["ok"] is False
        assert "not in the allowed_chat_ids" in result["error"]

    @pytest.mark.asyncio
    async def test_send_message_rejects_invalid_parse_mode(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.messaging import register_messaging_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_messaging_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["send_message"].fn(
            chat_id=111,
            text="Hello test",
            parse_mode="invalid",
        )
        assert result["ok"] is False
        assert "parse_mode must be one of" in result["error"]

    @pytest.mark.asyncio
    async def test_send_message_telegram_forbidden(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.messaging import register_messaging_tools

        mock_bot.send_message = AsyncMock(
            side_effect=TelegramForbiddenError(method=MagicMock(), message="Forbidden")
        )
        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_messaging_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["send_message"].fn(chat_id=111, text="Hello")
        assert result["ok"] is False
        assert "blocked" in result["error"].lower() or "permission" in result["error"].lower()

    @pytest.mark.asyncio
    async def test_send_message_telegram_bad_request(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.messaging import register_messaging_tools

        mock_bot.send_message = AsyncMock(
            side_effect=TelegramBadRequest(method=MagicMock(), message="Bad Request: chat not found")
        )
        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_messaging_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["send_message"].fn(chat_id=111, text="Hello")
        assert result["ok"] is False


class TestSendPhoto:
    @pytest.mark.asyncio
    async def test_send_photo_success(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.messaging import register_messaging_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_messaging_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["send_photo"].fn(
            chat_id=111, photo_url="https://example.com/photo.jpg"
        )
        assert result["ok"] is True
        assert result["message_id"] == 43

    @pytest.mark.asyncio
    async def test_send_photo_blocked_by_allowlist(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.messaging import register_messaging_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp, allowed_chat_ids=[111])
        register_messaging_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["send_photo"].fn(
            chat_id=999, photo_url="https://example.com/photo.jpg"
        )
        assert result["ok"] is False


class TestForwardMessage:
    @pytest.mark.asyncio
    async def test_forward_message_success(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.messaging import register_messaging_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_messaging_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["forward_message"].fn(
            to_chat_id=111, from_chat_id=222, message_id=1
        )
        assert result["ok"] is True
        assert result["message_id"] == 44

    @pytest.mark.asyncio
    async def test_forward_message_blocked(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.messaging import register_messaging_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp, allowed_chat_ids=[111])
        register_messaging_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["forward_message"].fn(
            to_chat_id=999, from_chat_id=111, message_id=1
        )
        assert result["ok"] is False


class TestDeleteMessage:
    @pytest.mark.asyncio
    async def test_delete_message_success(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.messaging import register_messaging_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_messaging_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["delete_message"].fn(chat_id=111, message_id=42)
        assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_delete_message_blocked(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.messaging import register_messaging_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp, allowed_chat_ids=[111])
        register_messaging_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["delete_message"].fn(chat_id=999, message_id=42)
        assert result["ok"] is False


class TestPinMessage:
    @pytest.mark.asyncio
    async def test_pin_message_success(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.messaging import register_messaging_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_messaging_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["pin_message"].fn(chat_id=111, message_id=42)
        assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_pin_message_blocked(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.messaging import register_messaging_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp, allowed_chat_ids=[111])
        register_messaging_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["pin_message"].fn(chat_id=999, message_id=42)
        assert result["ok"] is False


# ---------------------------------------------------------------------------
# User tools
# ---------------------------------------------------------------------------


class TestGetBotInfo:
    @pytest.mark.asyncio
    async def test_get_bot_info_success(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.users import register_user_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_user_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["get_bot_info"].fn()
        assert result["ok"] is True
        assert result["id"] == 123456789
        assert result["username"] == "test_bot"
        assert result["is_bot"] is True


class TestGetChatMemberInfo:
    @pytest.mark.asyncio
    async def test_get_chat_member_info_success(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.users import register_user_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_user_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["get_chat_member_info"].fn(chat_id=111, user_id=555)
        assert result["ok"] is True
        assert result["user_id"] == 555
        assert result["status"] == "member"
        assert result["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_get_chat_member_info_blocked(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.users import register_user_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp, allowed_chat_ids=[111])
        register_user_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["get_chat_member_info"].fn(chat_id=999, user_id=555)
        assert result["ok"] is False

    @pytest.mark.asyncio
    async def test_get_chat_member_info_telegram_error(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.users import register_user_tools

        mock_bot.get_chat_member = AsyncMock(
            side_effect=TelegramBadRequest(method=MagicMock(), message="user not found")
        )
        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_user_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["get_chat_member_info"].fn(chat_id=111, user_id=999)
        assert result["ok"] is False


class TestGetUserProfilePhotos:
    @pytest.mark.asyncio
    async def test_get_user_profile_photos_success(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.users import register_user_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_user_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["get_user_profile_photos"].fn(user_id=555)
        assert result["ok"] is True
        assert result["total_count"] == 1
        assert len(result["photos"]) == 1
        assert result["photos"][0][0]["file_id"] == "photo_id_1"

    @pytest.mark.asyncio
    async def test_get_user_profile_photos_invalid_limit(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.users import register_user_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_user_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["get_user_profile_photos"].fn(user_id=555, limit=0)
        assert result["ok"] is False
        assert "limit" in result["error"]

    @pytest.mark.asyncio
    async def test_get_user_profile_photos_limit_too_high(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.users import register_user_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_user_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["get_user_profile_photos"].fn(user_id=555, limit=101)
        assert result["ok"] is False


# ---------------------------------------------------------------------------
# Chat tools
# ---------------------------------------------------------------------------


class TestGetChatInfo:
    @pytest.mark.asyncio
    async def test_get_chat_info_success(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.chats import register_chat_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_chat_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["get_chat_info"].fn(chat_id=-1001234)
        assert result["ok"] is True
        assert result["type"] == "supergroup"
        assert result["title"] == "Test Group"
        assert result["member_count"] == 42

    @pytest.mark.asyncio
    async def test_get_chat_info_telegram_error(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.chats import register_chat_tools

        mock_bot.get_chat = AsyncMock(
            side_effect=TelegramBadRequest(method=MagicMock(), message="chat not found")
        )
        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_chat_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["get_chat_info"].fn(chat_id=999)
        assert result["ok"] is False


class TestGetChatMembersCount:
    @pytest.mark.asyncio
    async def test_get_chat_members_count_success(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.chats import register_chat_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_chat_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["get_chat_members_count"].fn(chat_id=-1001234)
        assert result["ok"] is True
        assert result["count"] == 42

    @pytest.mark.asyncio
    async def test_get_chat_members_count_error(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.chats import register_chat_tools

        mock_bot.get_chat_member_count = AsyncMock(
            side_effect=TelegramForbiddenError(
                method=MagicMock(), message="Forbidden"
            )
        )
        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_chat_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["get_chat_members_count"].fn(chat_id=-1001234)
        assert result["ok"] is False


class TestBanUser:
    @pytest.mark.asyncio
    async def test_ban_user_permanent(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.chats import register_chat_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_chat_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["ban_user"].fn(chat_id=111, user_id=555)
        assert result["ok"] is True
        assert result["permanent"] is True
        assert result["until"] is None

    @pytest.mark.asyncio
    async def test_ban_user_temporary(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.chats import register_chat_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_chat_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["ban_user"].fn(
            chat_id=111, user_id=555, ban_duration_hours=24
        )
        assert result["ok"] is True
        assert result["permanent"] is False
        assert result["until"] is not None

    @pytest.mark.asyncio
    async def test_ban_user_blocked_by_allowlist(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.chats import register_chat_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp, allowed_chat_ids=[111])
        register_chat_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["ban_user"].fn(chat_id=999, user_id=555)
        assert result["ok"] is False

    @pytest.mark.asyncio
    async def test_ban_user_telegram_error(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.chats import register_chat_tools

        mock_bot.ban_chat_member = AsyncMock(
            side_effect=TelegramBadRequest(
                method=MagicMock(), message="not enough rights"
            )
        )
        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_chat_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["ban_user"].fn(chat_id=111, user_id=555)
        assert result["ok"] is False


class TestUnbanUser:
    @pytest.mark.asyncio
    async def test_unban_user_success(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.chats import register_chat_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_chat_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["unban_user"].fn(chat_id=111, user_id=555)
        assert result["ok"] is True
        assert result["user_id"] == 555

    @pytest.mark.asyncio
    async def test_unban_user_blocked_by_allowlist(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.chats import register_chat_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp, allowed_chat_ids=[111])
        register_chat_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["unban_user"].fn(chat_id=999, user_id=555)
        assert result["ok"] is False


class TestSetChatTitle:
    @pytest.mark.asyncio
    async def test_set_chat_title_success(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.chats import register_chat_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_chat_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["set_chat_title"].fn(chat_id=111, title="New Title")
        assert result["ok"] is True
        assert result["new_title"] == "New Title"

    @pytest.mark.asyncio
    async def test_set_chat_title_blocked(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.chats import register_chat_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp, allowed_chat_ids=[111])
        register_chat_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["set_chat_title"].fn(chat_id=999, title="Hack")
        assert result["ok"] is False


class TestSetChatDescription:
    @pytest.mark.asyncio
    async def test_set_chat_description_success(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.chats import register_chat_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_chat_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["set_chat_description"].fn(
            chat_id=111, description="New desc"
        )
        assert result["ok"] is True

    @pytest.mark.asyncio
    async def test_set_chat_description_blocked(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.chats import register_chat_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp, allowed_chat_ids=[111])
        register_chat_tools(fast_mcp, tool_ctx)

        tools = await get_tool_map(fast_mcp)
        result = await tools["set_chat_description"].fn(
            chat_id=999, description="Hack"
        )
        assert result["ok"] is False


# ---------------------------------------------------------------------------
# Broadcast tools
# ---------------------------------------------------------------------------


class TestBroadcast:
    @pytest.mark.asyncio
    async def test_broadcast_dry_run_preview(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.broadcast import register_broadcast_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp, allowed_chat_ids=[111, 222])
        register_broadcast_tools(fast_mcp, tool_ctx, max_recipients=10)

        tools = await get_tool_map(fast_mcp)
        result = await tools["broadcast"].fn(chat_ids=[111, 222], text="Planned maintenance")

        assert result["ok"] is True
        assert result["dry_run"] is True
        assert result["would_send_to"] == 2

    @pytest.mark.asyncio
    async def test_broadcast_exceeds_recipient_limit(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.broadcast import register_broadcast_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_broadcast_tools(fast_mcp, tool_ctx, max_recipients=2)

        tools = await get_tool_map(fast_mcp)
        result = await tools["broadcast"].fn(
            chat_ids=[1, 2, 3], text="Too many"
        )
        assert result["ok"] is False
        assert "exceeds safety limit" in result["error"]

    @pytest.mark.asyncio
    async def test_broadcast_blocked_chats(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.broadcast import register_broadcast_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp, allowed_chat_ids=[111])
        register_broadcast_tools(fast_mcp, tool_ctx, max_recipients=10)

        tools = await get_tool_map(fast_mcp)
        result = await tools["broadcast"].fn(
            chat_ids=[111, 999], text="Hello"
        )
        assert result["ok"] is False
        assert "not in allowed_chat_ids" in result["error"]

    @pytest.mark.asyncio
    async def test_broadcast_actual_send(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.broadcast import register_broadcast_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_broadcast_tools(fast_mcp, tool_ctx, max_recipients=10)

        tools = await get_tool_map(fast_mcp)
        result = await tools["broadcast"].fn(
            chat_ids=[111, 222],
            text="Hello everyone",
            dry_run=False,
            delay_seconds=0,
        )
        assert result["ok"] is True
        assert result["dry_run"] is False
        assert result["success_count"] == 2
        assert result["failed_count"] == 0

    @pytest.mark.asyncio
    async def test_broadcast_partial_failure(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.broadcast import register_broadcast_tools

        call_count = 0

        async def send_message_side_effect(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise TelegramForbiddenError(method=MagicMock(), message="Forbidden")
            return MagicMock(message_id=call_count)

        mock_bot.send_message = AsyncMock(side_effect=send_message_side_effect)

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_broadcast_tools(fast_mcp, tool_ctx, max_recipients=10)

        tools = await get_tool_map(fast_mcp)
        result = await tools["broadcast"].fn(
            chat_ids=[111, 222, 333],
            text="Hello",
            dry_run=False,
            delay_seconds=0,
        )
        assert result["ok"] is True
        assert result["success_count"] == 2
        assert result["failed_count"] == 1

    @pytest.mark.asyncio
    async def test_broadcast_invalid_parse_mode(self, mock_bot, mock_dp):
        from aiogram_mcp.tools.broadcast import register_broadcast_tools

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_broadcast_tools(fast_mcp, tool_ctx, max_recipients=10)

        tools = await get_tool_map(fast_mcp)
        result = await tools["broadcast"].fn(
            chat_ids=[111],
            text="Hello",
            parse_mode="invalid",
            dry_run=False,
        )
        assert result["ok"] is False
        assert "parse_mode" in result["error"]


# ---------------------------------------------------------------------------
# Normalize parse mode
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# MCP Resources
# ---------------------------------------------------------------------------


class TestResourceBotInfo:
    @pytest.mark.asyncio
    async def test_bot_info_resource_registered(self, mock_bot, mock_dp):
        from aiogram_mcp.resources import register_resources

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_resources(fast_mcp, tool_ctx)

        resources = await fast_mcp.list_resources()
        uris = [str(r.uri) for r in resources]
        assert "telegram://bot/info" in uris

    @pytest.mark.asyncio
    async def test_bot_info_resource_content(self, mock_bot, mock_dp):
        import json

        from aiogram_mcp.resources import register_resources

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_resources(fast_mcp, tool_ctx)

        result = await fast_mcp.read_resource("telegram://bot/info")
        data = json.loads(result.contents[0].content)
        assert data["id"] == 123456789
        assert data["username"] == "test_bot"
        assert data["is_bot"] is True


class TestResourceConfig:
    @pytest.mark.asyncio
    async def test_config_resource_registered(self, mock_bot, mock_dp):
        from aiogram_mcp.resources import register_resources

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp, allowed_chat_ids=[111, 222])
        register_resources(fast_mcp, tool_ctx)

        resources = await fast_mcp.list_resources()
        uris = [str(r.uri) for r in resources]
        assert "telegram://config" in uris

    @pytest.mark.asyncio
    async def test_config_resource_content(self, mock_bot, mock_dp):
        import json

        from aiogram_mcp.resources import register_resources

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp, allowed_chat_ids=[111])
        register_resources(fast_mcp, tool_ctx)

        result = await fast_mcp.read_resource("telegram://config")
        data = json.loads(result.contents[0].content)
        assert data["allowed_chat_ids"] == [111]


class TestResourceChats:
    @pytest.mark.asyncio
    async def test_chats_resource_registered(self, mock_bot, mock_dp):
        from aiogram_mcp.resources import register_resources

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_resources(fast_mcp, tool_ctx)

        resources = await fast_mcp.list_resources()
        uris = [str(r.uri) for r in resources]
        assert "telegram://chats" in uris

    @pytest.mark.asyncio
    async def test_chats_without_middleware(self, mock_bot, mock_dp):
        import json

        from aiogram_mcp.resources import register_resources

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_resources(fast_mcp, tool_ctx)

        result = await fast_mcp.read_resource("telegram://chats")
        data = json.loads(result.contents[0].content)
        assert data["chats"] == []
        assert "note" in data

    @pytest.mark.asyncio
    async def test_chats_with_middleware(self, mock_bot, mock_dp):
        import json

        from aiogram_mcp.resources import register_resources

        mw = MCPMiddleware()
        mw.active_chat_ids = {-1001234}
        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp, middleware=mw)
        register_resources(fast_mcp, tool_ctx)

        result = await fast_mcp.read_resource("telegram://chats")
        data = json.loads(result.contents[0].content)
        assert len(data["chats"]) == 1
        assert data["chats"][0]["title"] == "Test Group"

    @pytest.mark.asyncio
    async def test_chats_filtered_by_allowlist(self, mock_bot, mock_dp):
        import json

        from aiogram_mcp.resources import register_resources

        mw = MCPMiddleware()
        mw.active_chat_ids = {111, 999}
        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(
            bot=mock_bot, dp=mock_dp, middleware=mw, allowed_chat_ids=[111]
        )
        register_resources(fast_mcp, tool_ctx)

        result = await fast_mcp.read_resource("telegram://chats")
        data = json.loads(result.contents[0].content)
        chat_ids = [c["id"] for c in data["chats"]]
        assert 999 not in chat_ids


class TestResourceChatHistory:
    @pytest.mark.asyncio
    async def test_history_resource_template(self, mock_bot, mock_dp):
        from aiogram_mcp.resources import register_resources

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_resources(fast_mcp, tool_ctx)

        templates = await fast_mcp.list_resource_templates()
        uris = [str(t.uri_template) for t in templates]
        assert any("chat_id" in u for u in uris)

    @pytest.mark.asyncio
    async def test_history_with_messages(self, mock_bot, mock_dp):
        import json
        from collections import deque

        from aiogram_mcp.resources import register_resources

        mw = MCPMiddleware()
        mw.message_history[111] = deque([
            {"message_id": 1, "from_user_id": 222, "from_username": "alice",
             "text": "Hello", "date": "2026-03-07T12:00:00"},
        ])
        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp, middleware=mw)
        register_resources(fast_mcp, tool_ctx)

        result = await fast_mcp.read_resource("telegram://chats/111/history")
        data = json.loads(result.contents[0].content)
        assert data["chat_id"] == 111
        assert len(data["messages"]) == 1
        assert data["messages"][0]["text"] == "Hello"

    @pytest.mark.asyncio
    async def test_history_blocked_by_allowlist(self, mock_bot, mock_dp):
        import json

        from aiogram_mcp.resources import register_resources

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(
            bot=mock_bot, dp=mock_dp, allowed_chat_ids=[111]
        )
        register_resources(fast_mcp, tool_ctx)

        result = await fast_mcp.read_resource("telegram://chats/999/history")
        data = json.loads(result.contents[0].content)
        assert data["ok"] is False

    @pytest.mark.asyncio
    async def test_history_without_middleware(self, mock_bot, mock_dp):
        import json

        from aiogram_mcp.resources import register_resources

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_resources(fast_mcp, tool_ctx)

        result = await fast_mcp.read_resource("telegram://chats/111/history")
        data = json.loads(result.contents[0].content)
        assert data["messages"] == []
        assert "note" in data


# ---------------------------------------------------------------------------
# Normalize parse mode
# ---------------------------------------------------------------------------


class TestNormalizeParseMode:
    def test_none_returns_none(self):
        from aiogram_mcp.tools.messaging import _normalize_parse_mode

        assert _normalize_parse_mode(None) is None

    def test_html(self):
        from aiogram.enums import ParseMode

        from aiogram_mcp.tools.messaging import _normalize_parse_mode

        assert _normalize_parse_mode("HTML") == ParseMode.HTML
        assert _normalize_parse_mode("html") == ParseMode.HTML
        assert _normalize_parse_mode("  Html  ") == ParseMode.HTML

    def test_markdown(self):
        from aiogram.enums import ParseMode

        from aiogram_mcp.tools.messaging import _normalize_parse_mode

        assert _normalize_parse_mode("Markdown") == ParseMode.MARKDOWN_V2
        assert _normalize_parse_mode("MarkdownV2") == ParseMode.MARKDOWN_V2

    def test_invalid_raises(self):
        from aiogram_mcp.tools.messaging import _normalize_parse_mode

        with pytest.raises(ValueError):
            _normalize_parse_mode("xml")


# ---------------------------------------------------------------------------
# MCP Prompts
# ---------------------------------------------------------------------------


class TestModerationPrompt:
    @pytest.mark.asyncio
    async def test_registered(self, mock_bot, mock_dp):
        from aiogram_mcp.prompts import register_prompts

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_prompts(fast_mcp, tool_ctx)

        prompts = await fast_mcp.list_prompts()
        names = [p.name for p in prompts]
        assert "moderation_prompt" in names

    @pytest.mark.asyncio
    async def test_content_with_valid_data(self, mock_bot, mock_dp):
        from collections import deque

        from aiogram_mcp.prompts import register_prompts

        mw = MCPMiddleware()
        mw.message_history[111] = deque([
            {"message_id": 1, "from_user_id": 555, "from_username": "testuser",
             "text": "bad message", "date": "2026-03-07T12:00:00"},
            {"message_id": 2, "from_user_id": 999, "from_username": "other",
             "text": "innocent", "date": "2026-03-07T12:01:00"},
        ])
        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp, middleware=mw)
        register_prompts(fast_mcp, tool_ctx)

        result = await fast_mcp.render_prompt(
            "moderation_prompt",
            {"chat_id": "111", "user_id": "555", "reason": "spam"},
        )
        text = result.messages[0].content.text
        assert "moderator" in text
        assert "spam" in text
        assert "bad message" in text
        # Should NOT include messages from other users
        assert "innocent" not in text

    @pytest.mark.asyncio
    async def test_chat_not_allowed(self, mock_bot, mock_dp):
        import json

        from aiogram_mcp.prompts import register_prompts

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(
            bot=mock_bot, dp=mock_dp, allowed_chat_ids=[111]
        )
        register_prompts(fast_mcp, tool_ctx)

        result = await fast_mcp.render_prompt(
            "moderation_prompt",
            {"chat_id": "999", "user_id": "555", "reason": "spam"},
        )
        data = json.loads(result.messages[0].content.text)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_without_middleware(self, mock_bot, mock_dp):
        from aiogram_mcp.prompts import register_prompts

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_prompts(fast_mcp, tool_ctx)

        result = await fast_mcp.render_prompt(
            "moderation_prompt",
            {"chat_id": "111", "user_id": "555", "reason": "spam"},
        )
        text = result.messages[0].content.text
        assert "moderator" in text
        assert "[]" in text  # empty recent messages

    @pytest.mark.asyncio
    async def test_includes_available_actions(self, mock_bot, mock_dp):
        from aiogram_mcp.prompts import register_prompts

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_prompts(fast_mcp, tool_ctx)

        result = await fast_mcp.render_prompt(
            "moderation_prompt",
            {"chat_id": "111", "user_id": "555", "reason": "test"},
        )
        text = result.messages[0].content.text
        assert "ban_user" in text
        assert "send_message" in text


class TestAnnouncementPrompt:
    @pytest.mark.asyncio
    async def test_registered(self, mock_bot, mock_dp):
        from aiogram_mcp.prompts import register_prompts

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_prompts(fast_mcp, tool_ctx)

        prompts = await fast_mcp.list_prompts()
        names = [p.name for p in prompts]
        assert "announcement_prompt" in names

    @pytest.mark.asyncio
    async def test_content_with_defaults(self, mock_bot, mock_dp):
        from aiogram_mcp.prompts import register_prompts

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_prompts(fast_mcp, tool_ctx)

        result = await fast_mcp.render_prompt(
            "announcement_prompt",
            {"topic": "Server maintenance"},
        )
        text = result.messages[0].content.text
        assert "Server maintenance" in text
        assert "all members" in text  # default audience
        assert "friendly" in text  # default tone
        assert "HTML" in text

    @pytest.mark.asyncio
    async def test_content_with_custom_params(self, mock_bot, mock_dp):
        from aiogram_mcp.prompts import register_prompts

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_prompts(fast_mcp, tool_ctx)

        result = await fast_mcp.render_prompt(
            "announcement_prompt",
            {"topic": "New feature", "audience": "admins", "tone": "formal"},
        )
        text = result.messages[0].content.text
        assert "New feature" in text
        assert "admins" in text
        assert "formal" in text

    @pytest.mark.asyncio
    async def test_includes_formatting_guidelines(self, mock_bot, mock_dp):
        from aiogram_mcp.prompts import register_prompts

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_prompts(fast_mcp, tool_ctx)

        result = await fast_mcp.render_prompt(
            "announcement_prompt",
            {"topic": "test"},
        )
        text = result.messages[0].content.text
        assert "parse_mode" in text
        assert "disable_notification" in text
        assert "send_message" in text


class TestUserReportPrompt:
    @pytest.mark.asyncio
    async def test_registered(self, mock_bot, mock_dp):
        from aiogram_mcp.prompts import register_prompts

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_prompts(fast_mcp, tool_ctx)

        prompts = await fast_mcp.list_prompts()
        names = [p.name for p in prompts]
        assert "user_report_prompt" in names

    @pytest.mark.asyncio
    async def test_content_with_valid_data(self, mock_bot, mock_dp):
        from collections import deque

        from aiogram_mcp.prompts import register_prompts

        mw = MCPMiddleware()
        mw.message_history[111] = deque([
            {"message_id": 1, "from_user_id": 555, "from_username": "testuser",
             "text": "Hello", "date": "2026-03-07T12:00:00"},
            {"message_id": 2, "from_user_id": 555, "from_username": "testuser",
             "text": "World", "date": "2026-03-07T12:01:00"},
        ])
        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp, middleware=mw)
        register_prompts(fast_mcp, tool_ctx)

        result = await fast_mcp.render_prompt(
            "user_report_prompt",
            {"chat_id": "111", "user_id": "555"},
        )
        text = result.messages[0].content.text
        assert "analyst" in text
        assert "message_count" in text
        assert '"message_count": 2' in text
        assert "Hello" in text
        assert "World" in text

    @pytest.mark.asyncio
    async def test_chat_not_allowed(self, mock_bot, mock_dp):
        import json

        from aiogram_mcp.prompts import register_prompts

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(
            bot=mock_bot, dp=mock_dp, allowed_chat_ids=[111]
        )
        register_prompts(fast_mcp, tool_ctx)

        result = await fast_mcp.render_prompt(
            "user_report_prompt",
            {"chat_id": "999", "user_id": "555"},
        )
        data = json.loads(result.messages[0].content.text)
        assert "error" in data

    @pytest.mark.asyncio
    async def test_without_middleware(self, mock_bot, mock_dp):
        from aiogram_mcp.prompts import register_prompts

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_prompts(fast_mcp, tool_ctx)

        result = await fast_mcp.render_prompt(
            "user_report_prompt",
            {"chat_id": "111", "user_id": "555"},
        )
        text = result.messages[0].content.text
        assert "analyst" in text
        assert '"message_count": 0' in text

    @pytest.mark.asyncio
    async def test_includes_profile_photos(self, mock_bot, mock_dp):
        from aiogram_mcp.prompts import register_prompts

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_prompts(fast_mcp, tool_ctx)

        result = await fast_mcp.render_prompt(
            "user_report_prompt",
            {"chat_id": "111", "user_id": "555"},
        )
        text = result.messages[0].content.text
        assert "Total: 1" in text  # mock returns total_count=1


class TestAllPromptsRegistered:
    @pytest.mark.asyncio
    async def test_three_prompts_in_list(self, mock_bot, mock_dp):
        from aiogram_mcp.prompts import register_prompts

        fast_mcp = _make_fast_mcp()
        tool_ctx = BotContext(bot=mock_bot, dp=mock_dp)
        register_prompts(fast_mcp, tool_ctx)

        prompts = await fast_mcp.list_prompts()
        names = {p.name for p in prompts}
        assert names == {"moderation_prompt", "announcement_prompt", "user_report_prompt"}

    @pytest.mark.asyncio
    async def test_prompts_via_server(self, mock_bot, mock_dp):
        """Prompts are registered when AiogramMCP is instantiated."""
        server = AiogramMCP(bot=mock_bot, dp=mock_dp)
        prompts = await server.fastmcp.list_prompts()
        names = {p.name for p in prompts}
        assert "moderation_prompt" in names
        assert "announcement_prompt" in names
        assert "user_report_prompt" in names


# ---------------------------------------------------------------------------
# Event Manager
# ---------------------------------------------------------------------------


class TestEventManager:
    def test_initial_state(self):
        em = EventManager()
        assert em.get_events() == []
        assert em.queue_size == 200

    def test_custom_queue_size(self):
        em = EventManager(queue_size=10)
        assert em.queue_size == 10

    @pytest.mark.asyncio
    async def test_push_event_adds_to_queue(self):
        em = EventManager(queue_size=100)
        await em.push_event({
            "type": "message",
            "chat_id": 111,
            "text": "Hello",
        })
        events = em.get_events()
        assert len(events) == 1
        assert events[0]["id"] == 1
        assert events[0]["type"] == "message"
        assert events[0]["chat_id"] == 111

    @pytest.mark.asyncio
    async def test_push_event_increments_id(self):
        em = EventManager(queue_size=100)
        await em.push_event({"type": "message", "chat_id": 111, "text": "A"})
        await em.push_event({"type": "message", "chat_id": 111, "text": "B"})
        events = em.get_events()
        assert events[0]["id"] == 1
        assert events[1]["id"] == 2

    @pytest.mark.asyncio
    async def test_get_events_since_id(self):
        em = EventManager(queue_size=100)
        await em.push_event({"type": "message", "chat_id": 111, "text": "A"})
        await em.push_event({"type": "message", "chat_id": 111, "text": "B"})
        await em.push_event({"type": "message", "chat_id": 111, "text": "C"})
        events = em.get_events(since_id=1)
        assert len(events) == 2
        assert events[0]["text"] == "B"

    @pytest.mark.asyncio
    async def test_queue_respects_max_size(self):
        em = EventManager(queue_size=3)
        for i in range(5):
            await em.push_event({"type": "message", "chat_id": 111, "text": f"msg-{i}"})
        events = em.get_events()
        assert len(events) == 3
        assert events[0]["text"] == "msg-2"


class TestEventManagerSubscriptions:
    def test_subscribe_returns_id(self):
        em = EventManager()
        sub_id = em.subscribe(chat_ids=[111], event_types=["message"])
        assert isinstance(sub_id, str)
        assert len(sub_id) == 12

    def test_unsubscribe_existing(self):
        em = EventManager()
        sub_id = em.subscribe()
        assert em.unsubscribe(sub_id) is True

    def test_unsubscribe_nonexistent(self):
        em = EventManager()
        assert em.unsubscribe("nonexistent") is False

    def test_matches_all_when_no_filters(self):
        em = EventManager()
        sub = Subscription(id="test")
        assert em._matches({"type": "message", "chat_id": 111}, sub) is True

    def test_matches_chat_filter(self):
        em = EventManager()
        sub = Subscription(id="test", chat_ids=[111])
        assert em._matches({"type": "message", "chat_id": 111}, sub) is True
        assert em._matches({"type": "message", "chat_id": 999}, sub) is False

    def test_matches_event_type_filter(self):
        em = EventManager()
        sub = Subscription(id="test", event_types=["command"])
        assert em._matches({"type": "command", "chat_id": 111}, sub) is True
        assert em._matches({"type": "message", "chat_id": 111}, sub) is False

    def test_matches_combined_filters(self):
        em = EventManager()
        sub = Subscription(id="test", chat_ids=[111], event_types=["command"])
        assert em._matches({"type": "command", "chat_id": 111}, sub) is True
        assert em._matches({"type": "message", "chat_id": 111}, sub) is False
        assert em._matches({"type": "command", "chat_id": 999}, sub) is False

    @pytest.mark.asyncio
    async def test_push_notifies_matching_subscriber(self):
        em = EventManager()
        session = AsyncMock()
        em.subscribe(chat_ids=[111], event_types=["message"], session=session)
        await em.push_event({"type": "message", "chat_id": 111, "text": "hi"})
        session.send_resource_updated.assert_called_once_with("telegram://events/queue")

    @pytest.mark.asyncio
    async def test_push_skips_non_matching_subscriber(self):
        em = EventManager()
        session = AsyncMock()
        em.subscribe(chat_ids=[999], event_types=["message"], session=session)
        await em.push_event({"type": "message", "chat_id": 111, "text": "hi"})
        session.send_resource_updated.assert_not_called()

    @pytest.mark.asyncio
    async def test_dead_session_removed(self):
        em = EventManager()
        session = AsyncMock()
        session.send_resource_updated.side_effect = Exception("closed")
        sub_id = em.subscribe(session=session)
        await em.push_event({"type": "message", "chat_id": 111, "text": "hi"})
        assert em.unsubscribe(sub_id) is False  # already removed
