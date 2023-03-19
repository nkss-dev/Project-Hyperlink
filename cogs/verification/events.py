import discord
from discord.ext import commands

from cogs.verification.ui import VerificationView
from main import ProjectHyperlink
from utils.utils import assign_student_roles

GUILD_IDS = {
    904633974306005033: 0,
    783215699707166760: 2024,
    915517972594982942: 2025,
}


class VerificationEvents(commands.Cog):
    """Exclusively manage verification events"""

    def __init__(self, bot: ProjectHyperlink):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        if member.guild.id not in GUILD_IDS:
            return

        guild = member.guild
        self.l10n = await self.bot.get_l10n(guild.id)

        channel = discord.utils.get(guild.text_channels, name="verify-here")
        if channel is None:
            self.bot.logger.critical(
                f"Verification channel not found for the guild **{guild.name}**!"
            )
            return

        # TODO: Fetch to breadboard instead
        student = await self.bot.pool.fetchrow(
            """
            SELECT
                section,
                email,
                batch,
                hostel_id,
                is_verified
            FROM
                student
            WHERE
                discord_id = $1
            """,
            member.id,
        )

        # TODO: Remove `is_verified` column from the database
        if student and student["is_verified"]:
            if GUILD_IDS[guild.id] != 0 and GUILD_IDS[guild.id] != student["batch"]:
                message = self.l10n.format_value("incorrect server")
                await member.send(message)
                await member.kick(reason=message)
                return

            await assign_student_roles(
                member,
                (
                    student["section"][:2],
                    student["batch"],
                    student["hostel_id"],
                ),
                self.bot.pool,
            )
            return

        view = VerificationView(
            self.l10n.format_value("verify-button-label"),
            self.bot,
            self.l10n.format_value,
        )
        await channel.send(
            self.l10n.format_value("verification-prompt", {"member": member.mention}),
            view=view,
        )


async def setup(bot):
    await bot.add_cog(VerificationEvents(bot))
