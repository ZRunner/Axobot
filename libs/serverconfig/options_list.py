import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .converters import AllRepresentation

options: dict[str, "AllRepresentation"] = {
    "anti_caps_lock": {
        "type": "boolean",
        "default": False,
        "is_listed": True,
    },
    "anti_raid": {
        "type": "enum",
        "values": ["none", "smooth", "careful", "high", "extreme"],
        "default": "none",
        "is_listed": True,
    },
    "anti_scam": {
        "type": "boolean",
        "default": False,
        "is_listed": True,
    },
    "ban_allowed_roles": {
        "type": "roles_list",
        "min_count": 1,
        "max_count": 100,
        "allow_integrated_roles": True,
        "allow_everyone": True,
        "default": None,
        "is_listed": True,
    },
    "bot_news": {
        "type": "text_channel",
        "allow_threads": True,
        "allow_announcement_channels": True,
        "allow_non_nsfw_channels": True,
        "default": None,
        "is_listed": True,
    },
    "clear_allowed_roles": {
        "type": "roles_list",
        "min_count": 1,
        "max_count": 100,
        "allow_integrated_roles": True,
        "allow_everyone": True,
        "default": None,
        "is_listed": True,
    },
    "compress_help": {
        "type": "boolean",
        "default": False,
        "is_listed": True,
    },
    "delete_welcome_on_quick_leave": {
        "type": "boolean",
        "default": False,
        "is_listed": True,
    },
    "description": {
        "type": "text",
        "min_length": 0,
        "max_length": 1000,
        "default": None,
        "is_listed": True,
    },
    "enable_fun": {
        "type": "boolean",
        "default": True,
        "is_listed": True,
    },
    "enable_xp": {
        "type": "boolean",
        "default": False,
        "is_listed": True,
    },
    "help_in_dm": {
        "type": "boolean",
        "default": False,
        "is_listed": True,
    },
    "kick_allowed_roles": {
        "type": "roles_list",
        "min_count": 1,
        "max_count": 100,
        "allow_integrated_roles": True,
        "allow_everyone": True,
        "default": None,
        "is_listed": True,
    },
    "language": {
        "type": "enum",
        "values": ('fr', 'en', 'lolcat', 'fi', 'de', 'fr2'),
        "default": "en",
        "is_listed": True,
    },
    "leave": {
        "type": "text",
        "min_length": 0,
        "max_length": 1800,
        "default": None,
        "is_listed": True,
    },
    "levelup_channel": {
        "type": "levelup_channel",
        "default": "any",
        "is_listed": True,
    },
    "levelup_msg": {
        "type": "text",
        "min_length": 0,
        "max_length": 1800,
        "default": None,
        "is_listed": True,
    },
    "membercounter": {
        "type": "voice_channel",
        "allow_stage_channels": False,
        "allow_non_nsfw_channels": True,
        "default": None,
        "is_listed": True,
    },
    "morpion_emojis": {
        "type": "emojis_list",
        "min_count": 2,
        "max_count": 2,
        "default": ['🔴', '🔵'],
        "is_listed": True,
    },
    "mute_allowed_roles": {
        "type": "roles_list",
        "min_count": 1,
        "max_count": 100,
        "allow_integrated_roles": True,
        "allow_everyone": True,
        "default": None,
        "is_listed": True,
    },
    "muted_role": {
        "type": "role",
        "allow_integrated_roles": False,
        "allow_everyone": False,
        "default": None,
        "is_listed": True,
    },
    "nicknames_history": {
        "type": "boolean",
        "default": False,
        "is_listed": False,
    },
    "noxp_channels": {
        "type": "text_channels_list",
        "min_count": 1,
        "max_count": 2000,
        "allow_threads": True,
        "allow_announcement_channels": True,
        "allow_non_nsfw_channels": True,
        "default": None,
        "is_listed": True,
    },
    "partner_channel": {
        "type": "text_channel",
        "allow_threads": True,
        "allow_announcement_channels": True,
        "allow_non_nsfw_channels": True,
        "default": None,
        "is_listed": True,
    },
    "partner_color": {
        "type": "color",
        "default": 0xA713FE,
        "is_listed": True,
    },
    "partner_role": {
        "type": "role",
        "allow_integrated_roles": False,
        "allow_everyone": False,
        "default": None,
        "is_listed": True,
    },
    "poll_channels": {
        "type": "text_channels_list",
        "min_count": 1,
        "max_count": 50,
        "allow_threads": True,
        "allow_announcement_channels": True,
        "allow_non_nsfw_channels": True,
        "default": None,
        "is_listed": True,
    },
    "prefix": {
        "type": "text",
        "min_length": 1,
        "max_length": 10,
        "default": "!",
        "is_listed": True,
    },
    "rank_in_dm": {
        "type": "boolean",
        "default": False,
        "is_listed": True,
    },
    "roles_react_max_number": {
        "type": "int",
        "min": 0,
        "max": math.inf,
        "default": 20,
        "is_listed": False,
    },
    "rr_max_number": {
        "type": "int",
        "min": 0,
        "max": math.inf,
        "default": 10,
        "is_listed": False,
    },
    "rss_max_number": {
        "type": "int",
        "min": 0,
        "max": math.inf,
        "default": 10,
        "is_listed": False,
    },
    "save_roles": {
        "type": "boolean",
        "default": False,
        "is_listed": False,
    },
    "say_allowed_roles": {
        "type": "roles_list",
        "min_count": 1,
        "max_count": 100,
        "allow_integrated_roles": True,
        "allow_everyone": True,
        "default": None,
        "is_listed": True,
    },
    "slowmode_allowed_roles": {
        "type": "roles_list",
        "min_count": 1,
        "max_count": 100,
        "allow_integrated_roles": True,
        "allow_everyone": True,
        "default": None,
        "is_listed": True,
    },
    "stream_mention": {
        "type": "role",
        "allow_integrated_roles": True,
        "allow_everyone": True,
        "default": None,
        "is_listed": True,
    },
     "streamers_max_number": {
        "type": "int",
        "min": 0,
        "max": math.inf,
        "default": 20,
        "is_listed": False,
    },
    "streaming_channel": {
        "type": "text_channel",
        "allow_threads": True,
        "allow_announcement_channels": True,
        "allow_non_nsfw_channels": True,
        "default": None,
        "is_listed": True,
    },
    "streaming_role": {
        "type": "role",
        "allow_integrated_roles": False,
        "allow_everyone": False,
        "default": None,
        "is_listed": True,
    },
    "ttt_display": {
        "type": "enum",
        "values": ["disabled", "short", "normal"],
        "default": "normal",
        "is_listed": True,
    },
    "update_mentions": {
        "type": "roles_list",
        "min_count": 1,
        "max_count": 10,
        "allow_integrated_roles": True,
        "allow_everyone": True,
        "default": None,
        "is_listed": False,
    },
    "voice_category": {
        "type": "category",
        "default": None,
        "is_listed": True,
    },
     "voice_channel": {
        "type": "voice_channel",
        "allow_stage_channels": False,
        "allow_non_nsfw_channels": True,
        "default": None,
        "is_listed": True,
    },
    "voice_channel_format": {
        "type": "text",
        "min_length": 1,
        "max_length": 50,
        "default": "{random}",
        "is_listed": True,
    },
    "voice_roles": {
        "type": "roles_list",
        "min_count": 1,
        "max_count": 10,
        "allow_integrated_roles": False,
        "allow_everyone": False,
        "default": None,
        "is_listed": True,
    },
    "vote_emojis": {
        "type": "emojis_list",
        "min_count": 2,
        "max_count": 2,
        "default": ['👍', '👎'],
        "is_listed": True,
    },
    "warn_allowed_roles": {
        "type": "roles_list",
        "min_count": 1,
        "max_count": 100,
        "allow_integrated_roles": True,
        "allow_everyone": True,
        "default": None,
        "is_listed": True,
    },
    "welcome": {
        "type": "text",
        "min_length": 0,
        "max_length": 1800,
        "default": None,
        "is_listed": True,
    },
    "welcome_channel": {
        "type": "text_channel",
        "allow_threads": False,
        "allow_announcement_channels": True,
        "allow_non_nsfw_channels": True,
        "default": None,
        "is_listed": True,
    },
    "welcome_roles": {
        "type": "roles_list",
        "min_count": 1,
        "max_count": 100,
        "allow_integrated_roles": False,
        "allow_everyone": False,
        "default": None,
        "is_listed": True,
    },
    "xp_rate": {
        "type": "float",
        "min": 0.1,
        "max": 3.0,
        "default": 1.0,
        "is_listed": True,
    },
    "xp_type": {
        "type": "enum",
        "values": ['global','mee6-like','local'],
        "default": "global",
        "is_listed": True,
    },
}
