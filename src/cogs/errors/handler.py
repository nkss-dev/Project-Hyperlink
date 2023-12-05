from typing import Any

import discord
from discord import app_commands
from discord.ext import commands

from . import app
from base.cog import HyperlinkCog
from base.context import HyperlinkContext
from main import ProjectHyperlink


class Errors(HyperlinkCog):
    """Global Error Handler"""

    def __init__(self, bot: ProjectHyperlink):
        super().__init__(bot)
        self.bot.tree.on_error = self.on_app_command_error

    @commands.Cog.listener()
    async def on_command_error(
        self,
        ctx: HyperlinkContext,
        error: commands.CommandError,
    ):
        l10n = await self.bot.get_l10n(ctx.guild.id if ctx.guild else 0)

        if isinstance(error, commands.UserInputError):
            if isinstance(error, commands.MissingRequiredArgument):
                await ctx.reply(
                    "UserInputError-MissingRequiredArgument",
                    l10n_context=dict(arg=error.param.name),
                )

            elif isinstance(error, commands.BadArgument):
                if isinstance(error, commands.MessageNotFound):
                    await ctx.reply(str(error))

                else:
                    await ctx.reply(str(error))

            elif isinstance(error, commands.BadUnionArgument):
                await ctx.reply(str(error))

            else:
                raise error

        elif isinstance(error, commands.CommandNotFound):
            pass

        elif isinstance(error, commands.CheckFailure):
            if isinstance(error, commands.NotOwner):
                await ctx.reply("Unauthorised-NotOwner")
            elif isinstance(error, app.NotInDevGuild):
                await ctx.reply("Unauthorised-NotInDevGuild")
            elif isinstance(error, commands.MissingPermissions):
                await ctx.reply(str(error))

            elif isinstance(error, commands.BotMissingPermissions):
                await ctx.reply(str(error))

            elif isinstance(error, commands.MissingAnyRole):
                assert ctx.guild is not None

                missing_roles = []
                for role_id in error.missing_roles:
                    role = ctx.guild.get_role(int(role_id))
                    if role is not None:
                        missing_roles.append(role.mention)
                        continue

                    self.logger.warning(
                        "Role id `{role_id}` not found in `{ctx.guild.name}`",
                        exc_info=True,
                    )

                # TODO: Ditch l10n
                embed = discord.Embed(
                    description=l10n.format_value(
                        "CheckFailure-MissingAnyRole",
                        {"roles": ", ".join(missing_roles)},
                    ),
                    color=discord.Color.blurple(),
                )
                await ctx.reply(embed=embed)

            else:
                prefix = ctx.clean_prefix
                help_str = prefix + self.bot.help_command.command_attrs["name"]
                variables = {"cmd": help_str, "member": f"`{ctx.author}`"}
                await ctx.reply(str(error), l10n_context=variables)

        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, discord.errors.Forbidden):
                await ctx.reply("CommandInvokeError-Forbidden")
            else:
                raise error

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(str(error))

        elif isinstance(error, commands.MaxConcurrencyReached):
            await ctx.reply(type(error).__name__)

        else:
            self.logger.exception(error)

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ):
        id = interaction.guild.id if interaction.guild else 0
        l10n = await self.bot.get_l10n(id)

        caught: bool = False
        error_text: str = error.__class__.__name__
        error_variables: dict[str, Any] = {}

        if isinstance(error, app.UnhandledError):
            caught = True

        elif isinstance(error, app_commands.CommandInvokeError):
            wrapped_error = error.__cause__

            if isinstance(wrapped_error, commands.ExtensionError):
                caught = True
                # TODO: Don't do this since it does not provide l10n
                error_text = str(wrapped_error)

        elif isinstance(error, app_commands.CheckFailure):
            caught = True
            error_variables = error.__dict__

            if isinstance(error, app_commands.MissingPermissions):
                # TODO: Don't do this since it does not provide l10n
                error_text = str(error)

        if not caught:
            self.logger.exception(error, extra={"user": interaction.user})

        if interaction.response.is_done():
            await interaction.followup.send(
                l10n.format_value(error_text, error_variables), ephemeral=True
            )
        else:
            await interaction.response.send_message(
                l10n.format_value(error_text, error_variables), ephemeral=True
            )


async def setup(bot: ProjectHyperlink):
    await bot.add_cog(Errors(bot))
