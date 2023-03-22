import discord
from discord import app_commands
from discord.ext import commands

from main import ProjectHyperlink


class Errors(commands.Cog):
    """Global Error Handler"""

    def __init__(self, bot: ProjectHyperlink):
        self.bot = bot
        self.bot.tree.on_error = self.on_app_command_error

    @commands.Cog.listener()
    async def on_command_error(
        self,
        ctx: commands.Context[ProjectHyperlink],
        error: commands.CommandError,
    ):
        l10n = await self.bot.get_l10n(ctx.guild.id if ctx.guild else 0)

        if isinstance(error, commands.UserInputError):
            if isinstance(error, commands.MissingRequiredArgument):
                await ctx.reply(
                    l10n.format_value(
                        "UserInputError-MissingRequiredArgument",
                        {"arg": error.param.name},
                    )
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
                await ctx.reply(l10n.format_value("CheckFailure-NotOwner"))

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

                    self.bot.logger.warning(
                        "Role id `{role_id}` not found in `{ctx.guild.name}`",
                        exc_info=True,
                    )

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
                await ctx.reply(l10n.format_value(str(error), variables))

        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, discord.errors.Forbidden):
                await ctx.reply(l10n.format_value("CommandInvokeError-Forbidden"))
            else:
                raise error

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(str(error))

        elif isinstance(error, commands.MaxConcurrencyReached):
            await ctx.reply(l10n.format_value(type(error).__name__))

        else:
            self.bot.logger.exception(error)

    async def on_app_command_error(
        self,
        interaction: discord.Interaction,
        error: app_commands.AppCommandError,
    ):
        id = interaction.guild.id if interaction.guild else 0
        l10n = await self.bot.get_l10n(id)

        if interaction.response.is_done():
            send_callback = interaction.followup.send
        else:
            send_callback = interaction.response.send_message

        if error.args[0] == "UnhandledError":
            await send_callback(l10n.format_value(error.args[0]), ephemeral=True)
            self.bot.logger.critical(
                "Unhandled Error",
                exc_info=True,
                extra={"user": interaction.user},
            )
            return

        error_text = error.args[0]
        error_variables = error.args[1] if len(error.args) > 1 else {}

        if isinstance(error, app_commands.CommandInvokeError):
            wrapped_error = error.__cause__

            if isinstance(wrapped_error, commands.ExtensionError):
                await send_callback(str(error.__cause__), ephemeral=True)
                return

        elif isinstance(error, app_commands.CheckFailure):
            if isinstance(error, app_commands.MissingPermissions):
                await send_callback(str(error), ephemeral=True)
                return

            await send_callback(
                l10n.format_value(error_text, error_variables), ephemeral=True
            )
            return

        self.bot.logger.exception(error)


async def setup(bot: ProjectHyperlink):
    await bot.add_cog(Errors(bot))
