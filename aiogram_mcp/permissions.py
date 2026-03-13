"""Permission levels for MCP tool access control."""

from __future__ import annotations

from enum import IntEnum


class PermissionLevel(IntEnum):
    """Hierarchical permission levels. Each includes all tools of levels below it."""

    READ = 1
    MESSAGING = 2
    MODERATION = 3
    ADMIN = 4


TOOL_PERMISSIONS: dict[str, PermissionLevel] = {
    # read (5 tools)
    "get_bot_info": PermissionLevel.READ,
    "get_chat_info": PermissionLevel.READ,
    "get_chat_member_info": PermissionLevel.READ,
    "get_user_profile_photos": PermissionLevel.READ,
    "get_chat_members_count": PermissionLevel.READ,
    # messaging (16 tools)
    "send_message": PermissionLevel.MESSAGING,
    "send_photo": PermissionLevel.MESSAGING,
    "forward_message": PermissionLevel.MESSAGING,
    "send_interactive_message": PermissionLevel.MESSAGING,
    "edit_message": PermissionLevel.MESSAGING,
    "answer_callback_query": PermissionLevel.MESSAGING,
    "send_document": PermissionLevel.MESSAGING,
    "send_voice": PermissionLevel.MESSAGING,
    "send_video": PermissionLevel.MESSAGING,
    "send_animation": PermissionLevel.MESSAGING,
    "send_audio": PermissionLevel.MESSAGING,
    "send_sticker": PermissionLevel.MESSAGING,
    "send_video_note": PermissionLevel.MESSAGING,
    "send_contact": PermissionLevel.MESSAGING,
    "send_location": PermissionLevel.MESSAGING,
    "send_poll": PermissionLevel.MESSAGING,
    # moderation (6 tools)
    "delete_message": PermissionLevel.MODERATION,
    "pin_message": PermissionLevel.MODERATION,
    "ban_user": PermissionLevel.MODERATION,
    "unban_user": PermissionLevel.MODERATION,
    "set_chat_title": PermissionLevel.MODERATION,
    "set_chat_description": PermissionLevel.MODERATION,
    # admin (3 tools)
    "broadcast": PermissionLevel.ADMIN,
    "subscribe_events": PermissionLevel.ADMIN,
    "unsubscribe_events": PermissionLevel.ADMIN,
}


def parse_permission_level(value: PermissionLevel | str) -> PermissionLevel:
    """Convert a string or PermissionLevel to PermissionLevel. Case-insensitive."""
    if isinstance(value, PermissionLevel):
        return value
    normalized = value.strip().upper()
    try:
        return PermissionLevel[normalized]
    except KeyError:
        valid = ", ".join(level.name.lower() for level in PermissionLevel)
        raise ValueError(f"Invalid permission level '{value}'. Valid: {valid}") from None


def get_allowed_tools(level: PermissionLevel) -> set[str]:
    """Return the set of tool names allowed at the given permission level."""
    return {name for name, min_level in TOOL_PERMISSIONS.items() if min_level <= level}
