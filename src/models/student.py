from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class Student:
    roll_number: str
    section: str
    name: str
    gender: Literal["F", "M", "O"] | None
    mobile: str | None
    birth_date: str | None
    email: str
    batch: int
    hostel_id: str
    room_id: str | None
    discord_id: int | None
    is_verified: bool
    clubs: list[dict[str, str]]
