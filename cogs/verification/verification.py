import asyncio

import config
import discord
from discord.ext import commands

import cogs.checks as checks
from . import GUILD_IDS
from cogs.errors.app import UserAlreadyVerified
from cogs.verification.ui import VerificationView
from cogs.verification.utils import assign_student_roles, verify
from main import ProjectHyperlink
from models.student import Student, parse_student


class Verification(commands.Cog):
    """The Great Wall of NITKKR"""

    def __init__(self, bot: ProjectHyperlink):
        self.bot = bot

    async def cog_load(self) -> None:
        club_guild_ids: list[dict[str, int]] = await self.bot.pool.fetch(
            """
            SELECT
                guild_id
            FROM
                club_discord
            """
        )
        self.club_guild_ids: list[int] = [
            club_guild_id["guild_id"] for club_guild_id in club_guild_ids
        ]

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

        verified = await checks._is_verified(interaction, True)
        if verified:
            raise UserAlreadyVerified

        await verify(self.bot, interaction, roll)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        async with self.bot.session.get(
            f"{config.api_url}/discord/users/{member.id}",
            headers={"Authorization": f"Bearer {config.api_token}"},
        ) as resp:
            if resp.status == 200:
                student_dict = (await resp.json())["data"]
            else:
                student_dict = {}

        student = parse_student(student_dict) if student_dict else None

        if member.guild.id in GUILD_IDS:
            self.bot.dispatch("member_join_nit", member, student)
            return

        if member.guild.id in self.club_guild_ids:
            self.bot.dispatch("member_join_club", member, student)

    @commands.Cog.listener()
    async def on_member_join_nit(self, member: discord.Member, student: Student | None):
        guild = member.guild
        self.l10n = await self.bot.get_l10n(guild.id)

        channel = discord.utils.get(guild.text_channels, name="verify-here")
        if channel is None:
            self.bot.logger.critical(
                f"Verification channel not found for the guild `{guild.name}`!"
            )
            return

        if student and student.is_verified:
            if GUILD_IDS[guild.id] != 0 and GUILD_IDS[guild.id] != student.batch:
                await member.send(
                    self.l10n.format_value(
                        "IncorrectGuildBatch",
                        {
                            "roll": student.roll_number,
                            "server_batch": GUILD_IDS[guild.id],
                            "student_batch": student.batch,
                        },
                    )
                )
                message = f"{member.mention} was kicked from `{guild.name}` due to incorrect guild"
                await member.kick(reason=message)
                self.bot.logger.info(message)
                return

            await assign_student_roles(student, member.guild)
            self.bot.logger.info(
                f"{member.mention} was provided direct access to `{guild.name}`"
            )
            return

        prompt = await channel.send(
            self.l10n.format_value("verification-prompt", {"member": member.mention}),
        )
        self.bot.logger.info(
            f"Verification prompt sent to new user in `{guild.name}`",
            extra={"user": member},
        )

        try:
            await self.bot.wait_for(
                "user_verify",
                check=lambda user: user.discord_id == member.id,
                timeout=1200.0,
            )
        except asyncio.TimeoutError:
            pass
        await prompt.delete()

    @commands.Cog.listener()
    async def on_user_verify(self, student: Student):
        # TODO: Loop through all guilds and perform role remove also
        for guild_id in GUILD_IDS:
            guild = self.bot.get_guild(guild_id)
            assert guild is not None

            if GUILD_IDS[guild_id] == 0 or GUILD_IDS[guild_id] == student.batch:
                await assign_student_roles(student, guild)

        if student.clubs:
            self.bot.dispatch("club_member_change", student)


async def setup(bot):
    await bot.add_cog(Verification(bot))
