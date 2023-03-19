import discord

import traceback

from main import ProjectHyperlink


class VerificationView(discord.ui.View):
    def __init__(self, label: str, bot: ProjectHyperlink):
        super().__init__()

        button = VerificationButton(label, bot)
        self.add_item(button)


class VerificationButton(discord.ui.Button):
    def __init__(self, label, bot: ProjectHyperlink, **kwargs):
        super().__init__(label=label, style=discord.ButtonStyle.green, **kwargs)
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_modal(VerificationModal(self.bot))


class VerificationModal(discord.ui.Modal, title="Verification"):
    roll = discord.ui.TextInput(
        label="Roll Number",
        placeholder="12022005",
        max_length=8,
    )

    def __init__(self, bot: ProjectHyperlink):
        super().__init__()
        self.bot = bot

    async def on_submit(self, interaction: discord.Interaction):
        student = await self.bot.pool.fetchrow(
            f"""
            SELECT
                name,
                email
            FROM
                student
            WHERE
                roll_number = $1
            """,
            self.roll.value,
        )
        if not student:
            await interaction.response.send_message(
                f"{self.roll.value} was not found in our database. Please try again with a correct roll number. If you think this was a mistake, contact a moderator",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"An OTP has been sent to `{student['email']}`! Please paste the OTP below",
            ephemeral=True,
        )

    async def on_error(
        self, interaction: discord.Interaction, error: Exception
    ) -> None:
        await interaction.response.send_message(
            "Oops! Something went wrong.", ephemeral=True
        )

        traceback.print_exception(type(error), error, error.__traceback__)
