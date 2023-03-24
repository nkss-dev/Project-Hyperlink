import config

from discord import app_commands, Interaction
from discord.ext import commands

from main import ProjectHyperlink


async def _is_verified(
    instance: commands.Context[ProjectHyperlink] | Interaction[ProjectHyperlink],
    suppress: bool = False,
):
    author, bot, error = (
        (instance.author, instance.bot, commands.CheckFailure)
        if isinstance(instance, commands.Context)
        else (instance.user, instance.client, app_commands.CheckFailure)
    )

    async with bot.session.get(
        f"{config.api_url}/status/student/discord", params={"id": author.id}
    ) as resp:
        if resp.status == 404:
            if suppress:
                return False
            else:
                raise error("AccountNotLinked")
        if (await resp.json())["data"] is False:
            if suppress:
                return False
            else:
                raise error("UserNotVerified")
    return True


async def _is_owner(
    instance: commands.Context[ProjectHyperlink] | Interaction[ProjectHyperlink],
    suppress: bool = False,
):
    author, bot, error = (
        (instance.author, instance.bot, commands.NotOwner)
        if isinstance(instance, commands.Context)
        else (
            instance.user,
            instance.client,
            app_commands.CheckFailure("Unauthorised-NotOwner"),
        )
    )

    if not await bot.is_owner(author):
        if suppress:
            return False
        raise error
    return True
