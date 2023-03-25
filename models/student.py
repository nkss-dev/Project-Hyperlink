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
    clubs: dict[str, str]


def parse_student(student: dict[str, Any]) -> Student:
    def is_valid(field: str, kind: str = "String"):
        if student[field]["Valid"]:
            return student.pop(field)[kind]
        return None

    student["gender"] = is_valid("gender")
    student["mobile"] = is_valid("mobile")
    student["birth_date"] = is_valid("birth_date", "Time")
    student["room_id"] = is_valid("room_id")
    student["discord_id"] = is_valid("discord_id", "Int64")

    return Student(**student)
