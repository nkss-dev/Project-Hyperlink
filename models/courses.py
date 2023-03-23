from dataclasses import dataclass
from typing import Literal


@dataclass
class Specifics:
    branch: Literal["CE", "CS", "EC", "EE", "IT", "ME", "PI"]
    semester: Literal[1, 2, 3, 4, 5, 6, 7, 8]
    credits: list[int]


@dataclass
class Course:
    code: str
    title: str
    prereq: list[str]
    kind: str
    objectives: list[str]
    content: list[str]
    book_names: list[str]
    outcomes: list[str]

    specifics: list[Specifics]
