from dataclasses import dataclass
from typing import Literal


@dataclass
class GuildEvent:
    guild_id: int
    event_type: Literal["ban", "join", "kick", "leave", "welcome"]
    channel_id: int
    message: str | None
