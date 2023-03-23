from typing import Any, TYPE_CHECKING

import discord
from discord.app_commands import AppCommandError

from cogs.verification.utils import verify

if TYPE_CHECKING:
    from main import ProjectHyperlink
else:
    ProjectHyperlink = discord.ext.commands.Bot


# TODO: Make view persistent
class VerificationView(discord.ui.View):
    def __init__(self, label: str, bot: ProjectHyperlink):
        super().__init__(timeout=None)
        self.bot = bot

        button = VerificationButton(label, bot)
        self.add_item(button)

    async def on_error(
        self,
        interaction: discord.Interaction[ProjectHyperlink],
        error: Exception,
        _: discord.ui.Item[Any],
    ) -> None:
        if isinstance(error, AppCommandError):
            await self.bot.tree.on_error(interaction, error)
        else:
            await self.bot.tree.on_error(
                interaction,
                AppCommandError("UnhandledError"),
            )


class VerificationButton(discord.ui.Button):
    def __init__(self, label, bot: ProjectHyperlink, **kwargs):
        super().__init__(label=label, style=discord.ButtonStyle.green, **kwargs)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        assert interaction.guild is not None
        assert isinstance(interaction.user, discord.Member)

        # TODO: Change this to use the check
        for role in interaction.user.roles:
            if role.name == "verified":
                self.bot.logger.info(
                    f"Verified user attempted to verify in `{interaction.guild.name}` using the verification button",
                    extra={"user": interaction.user},
                )
                raise discord.app_commands.CheckFailure("UserAlreadyVerified")

        await interaction.response.send_modal(VerificationModal(self.bot))


class VerificationModal(discord.ui.Modal, title="Verification"):
    roll = discord.ui.TextInput(
        label="Roll Number",
        placeholder="12022005",
        max_length=8,
        min_length=8,
    )

    def __init__(self, bot: ProjectHyperlink):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction[ProjectHyperlink]):
        assert isinstance(interaction.user, discord.Member)
        assert self.roll.value is not None

        await verify(self.bot, interaction, self.roll.value)

    async def on_error(
        self, interaction: discord.Interaction[ProjectHyperlink], error: Exception
    ) -> None:
        if isinstance(error, AppCommandError):
            await self.bot.tree.on_error(interaction, error)
        else:
            self.bot.logger.critical(error)
