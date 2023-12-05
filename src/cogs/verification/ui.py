from typing import Any, TYPE_CHECKING

import discord
from discord.app_commands import AppCommandError

import cogs.checks as checks
from cogs.errors.app import UnhandledError, UserAlreadyVerified
from cogs.verification.utils import verify

if TYPE_CHECKING:
    from main import ProjectHyperlink
else:
    ProjectHyperlink = discord.ext.commands.Bot


class VerificationView(discord.ui.View):
    def __init__(self, label: str):
        super().__init__(timeout=None)

        button = VerificationButton(label, custom_id="VerificationButton")
        self.add_item(button)

    async def on_error(
        self,
        interaction: discord.Interaction[ProjectHyperlink],
        error: Exception,
        _: discord.ui.Item[Any],
    ) -> None:
        if isinstance(error, AppCommandError):
            await interaction.client.tree.on_error(interaction, error)
        else:
            await interaction.client.tree.on_error(
                interaction,
                UnhandledError(),
            )


class VerificationButton(discord.ui.Button):
    def __init__(self, label, **kwargs):
        super().__init__(label=label, style=discord.ButtonStyle.green, **kwargs)

    async def callback(self, interaction: discord.Interaction[ProjectHyperlink]):
        assert interaction.guild is not None
        assert isinstance(interaction.user, discord.Member)

        verified = await checks._is_verified(interaction, True)
        if verified:
            raise UserAlreadyVerified

        await interaction.response.send_modal(VerificationModal(interaction.client))


class VerificationModal(discord.ui.Modal, title="Verification"):
    roll = discord.ui.TextInput(
        label="Roll Number",
        placeholder="12022005",
        max_length=9,
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
