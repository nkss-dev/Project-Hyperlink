from typing import Callable, TypeVar

from discord import app_commands
from discord.ext import commands

from .checks import _is_owner, _is_verified, _is_dev_guild

T = TypeVar("T")


def is_owner() -> Callable[[T], T]:
    def decorator(fn: T) -> T:
        app_commands.check(_is_owner)(fn)
        commands.check(_is_owner)(fn)
        return fn

    return decorator


def is_verified() -> Callable[[T], T]:
    def decorator(fn: T) -> T:
        app_commands.check(_is_verified)(fn)
        commands.check(_is_verified)(fn)
        return fn

    return decorator


def is_dev_guild() -> Callable[[T], T]:
    def decorator(fn: T) -> T:
        app_commands.check(_is_dev_guild)(fn)
        commands.check(_is_dev_guild)(fn)
        return fn

    return decorator
