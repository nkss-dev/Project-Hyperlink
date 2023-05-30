import config
from typing import TYPE_CHECKING

from discord import Interaction
from discord.ext import commands

from cogs.errors import app

if TYPE_CHECKING:
    from main import ProjectHyperlink
else:
    ProjectHyperlink = commands.Bot


async def _is_verified(
    instance: commands.Context[ProjectHyperlink] | Interaction[ProjectHyperlink],
    suppress: bool = False,
):
    author, bot, error = (
        (instance.author, instance.bot, commands.CheckFailure("UserNotVerified"))
        if isinstance(instance, commands.Context)
        else (instance.user, instance.client, app.UserNotVerified)
    )

    verified = False
    async with bot.session.get(
        f"{config.api_url}/status/student/discord", params=dict(id=author.id)
    ) as resp:
        if resp.status in range(500, 600):
            bot.logger.exception("API returned an error")
            raise app.UnhandledError
        elif resp.status == 200:
            verified = (await resp.json())["data"]

    if not verified and not suppress:
        raise error
    return verified


async def _is_owner(
    instance: commands.Context[ProjectHyperlink] | Interaction[ProjectHyperlink],
    *,
    message: str | None = None,
    suppress: bool = False,
):
    author, bot, error = (
        (instance.author, instance.bot, commands.NotOwner)
        if isinstance(instance, commands.Context)
        else (instance.user, instance.client, app.NotOwner)
    )

    if not await bot.is_owner(author):
        if suppress:
            return False
        if message is None:
            raise error
        raise error(message)
    return True


async def _is_dev_guild(
    instance: commands.Context[ProjectHyperlink] | Interaction[ProjectHyperlink],
    *,
    suppress: bool = False,
):
    guild_id, bot, error = (
        (instance.guild.id, instance.bot, commands.CheckFailure("NotInDevGuild"))
        if isinstance(instance, commands.Context)
        else (instance.guild.id, instance.client, app.NotInDevGuild)
    )

    if guild_id not in config.dev_guild_ids:
        if suppress:
            return False
        raise error

    return True
