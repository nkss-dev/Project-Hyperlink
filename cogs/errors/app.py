import discord
from discord.app_commands import AppCommandError, CheckFailure


class BatchNotFound(CheckFailure):
    def __init__(self, *, batch: int) -> None:
        self.batch = batch


class IncorrectGuildBatch(CheckFailure):
    def __init__(
        self, *, roll_number: str, server_batch: int, student_batch: int
    ) -> None:
        self.roll_number = roll_number
        self.server_batch = server_batch
        self.student_batch = student_batch


class NotForBot(CheckFailure):
    pass


class NotOwner(CheckFailure):
    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.__class__.__name__)


class OTPTimeout(CheckFailure):
    def __init__(self, *, member: discord.Member) -> None:
        self.member = member.mention


class RollNotFound(CheckFailure):
    def __init__(self, *, roll_number: str) -> None:
        self.roll_number = roll_number


class UnhandledError(AppCommandError):
    pass


class UserAlreadyVerified(CheckFailure):
    pass


class UserNotFound(CheckFailure):
    def __init__(self, *, member: discord.Member | discord.User) -> None:
        self.member = member.mention


class UserNotVerified(CheckFailure):
    pass
