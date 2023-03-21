from typing import Any

import discord

from cogs.verification.utils import authenticate, post_verification_handler
from main import ProjectHyperlink

GUILD_IDS = {
    904633974306005033: 0,
    783215699707166760: 2024,
    915517972594982942: 2025,
}


class VerificationView(discord.ui.View):
    def __init__(self, label: str, bot: ProjectHyperlink, fmv):
        super().__init__(timeout=None)
        self.bot = bot

        button = VerificationButton(label, bot, fmv)
        self.add_item(button)

    async def on_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
        _: discord.ui.Item[Any],
    ) -> None:
        await self.bot.tree.on_error(interaction, error)


class VerificationButton(discord.ui.Button):
    def __init__(self, label, bot: ProjectHyperlink, fmv, **kwargs):
        super().__init__(label=label, style=discord.ButtonStyle.green, **kwargs)
        self.bot = bot
        self.fmv = fmv

    async def callback(self, interaction: discord.Interaction):
        assert isinstance(interaction.user, discord.Member)

        # TODO: Change this to use the check
        for role in interaction.user.roles:
            if role.name == "verified":
                raise discord.app_commands.CheckFailure("UserAlreadyVerified")

        await interaction.response.send_modal(VerificationModal(self.bot, self.fmv))


class VerificationModal(discord.ui.Modal, title="Verification"):
    roll = discord.ui.TextInput(
        label="Roll Number",
        placeholder="12022005",
        max_length=8,
        min_length=8,
    )

    def __init__(self, bot: ProjectHyperlink, fmv):
        super().__init__()
        self.bot = bot
        self.fmv = fmv

    async def on_submit(self, interaction: discord.Interaction):
        # To please linter gods:
        assert isinstance(interaction.user, discord.Member)
        assert interaction.channel_id is not None
        assert self.roll.value is not None

        member = interaction.user

        student: dict[str, str] = await self.bot.pool.fetchrow(
            f"""
            SELECT
                roll_number,
                section,
                name,
                email,
                batch,
                hostel_id
            FROM
                student
            WHERE
                roll_number = $1
            """,
            self.roll.value,
        )
        if not student:
            raise discord.app_commands.CheckFailure(
                "NotFound-roll", {"roll": self.roll.value}
            )

        if (
            GUILD_IDS[member.guild.id] != 0
            and GUILD_IDS[member.guild.id] != student["batch"]
        ):
            raise discord.app_commands.CheckFailure(
                "BadRequest-incorrect-guild", {"batch": student["batch"]}
            )

        await interaction.response.send_message(
            self.fmv("email-sent", {"email": student["email"]}),
            ephemeral=True,
        )

        verified = await authenticate(
            self.roll.value,
            student["name"],
            student["email"],
            self.bot,
            member,
            interaction.channel_id,
            interaction.followup.send,
        )
        if verified is False:
            return

        await interaction.followup.send(
            self.fmv("verification-success", {"mention": member.mention})
        )

        await post_verification_handler(member, student, self.bot.pool)

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await self.bot.tree.on_error(interaction, error)
