import discord
from discord.ext import commands

import cogs.checks as checks
from . import GUILD_IDS
from cogs.verification.ui import VerificationView
from cogs.verification.utils import post_verification_handler, verify
from main import ProjectHyperlink


class Verification(commands.Cog):
    """The Great Wall of NITKKR"""

    def __init__(self, bot: ProjectHyperlink):
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        guild = interaction.guild
        l10n = await self.bot.get_l10n(guild.id if guild else 0)
        self.fmv = l10n.format_value
        return True

    @commands.command(hidden=True)
    @checks.is_owner()
    @commands.guild_only()
    async def verification(self, ctx: commands.Context[ProjectHyperlink]):
        """Send a verification button"""
        assert ctx.guild is not None

        if ctx.guild.id not in GUILD_IDS:
            return

        l10n = await self.bot.get_l10n(ctx.guild.id)
        view = VerificationView(l10n.format_value("verify-button-label"))

        await ctx.send(
            l10n.format_value("verification-message"),
            view=view,
        )
        await ctx.message.delete()

    @discord.app_commands.command(name="verify")
    @discord.app_commands.guild_only()
    async def verify_command(
        self, interaction: discord.Interaction[ProjectHyperlink], roll: str
    ):
        assert interaction.guild is not None
        assert isinstance(interaction.user, discord.Member)

        await checks._is_verified(interaction)

        await verify(self.bot, interaction, roll)

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
                f"Verification channel not found for the guild `{guild.name}`!"
            )
            return

        # TODO: Fetch to breadboard instead
        student: dict[str, str] = await self.bot.pool.fetchrow(
            """
            SELECT
                roll_number,
                section,
                name,
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
                await member.send(
                    self.l10n.format_value(
                        "IncorrectGuildBatch",
                        {
                            "roll": student["roll_number"],
                            "server_batch": GUILD_IDS[guild.id],
                            "student_batch": student["batch"],
                        },
                    )
                )
                message = f"{member.mention} was kicked from `{guild.name}` due to incorrect guild"
                await member.kick(reason=message)
                self.bot.logger.info(message)
                return

            await post_verification_handler(member, student, self.bot.pool)
            self.bot.logger.info(
                f"{member.mention} was provided direct access to `{guild.name}`"
            )
            return

        # TODO: Somehow delete this message once the user verifies
        await channel.send(
            self.l10n.format_value("verification-prompt", {"member": member.mention}),
        )
        self.bot.logger.info(
            f"Verification prompt sent to new user in `{guild.name}`",
            extra={"user": member},
        )


async def setup(bot):
    await bot.add_cog(Verification(bot))
