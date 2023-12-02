from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import config
import discord
from discord.ext import commands

import cogs.checks as checks
from base.cog import HyperlinkCog
from base.context import HyperlinkContext
from cogs.errors.app import UserAlreadyVerified
from cogs.verification.ui import VerificationView
from cogs.verification.utils import assign_student_roles, kick_old, verify
from models.student import Student

if TYPE_CHECKING:
    from main import ProjectHyperlink

NITKKR_GUILD_ID = 904633974306005033


class EntryPoint(HyperlinkCog):
    """Verification entry point"""

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

        affiliate_guild_ids: list[dict[str, int]] = await self.bot.pool.fetch(
            """
            SELECT
                DISTINCT guild_id
            FROM
                guild_role
            """
        )
        self.affiliate_guild_ids: list[int] = [
            affiliate_guild_id["guild_id"] for affiliate_guild_id in affiliate_guild_ids
        ]
        await super().cog_load()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        guild = interaction.guild
        l10n = await self.bot.get_l10n(guild.id if guild else 0)
        self.fmv = l10n.format_value
        return True

    @commands.command(hidden=True)
    @checks.is_owner()
    @commands.guild_only()
    async def verification(self, ctx: HyperlinkContext):
        """Send a verification button"""
        assert ctx.guild is not None

        l10n = await self.bot.get_l10n(ctx.guild.id)
        view = VerificationView(l10n.format_value("verify-button-label"))

        await ctx.send("verification-message", view=view)
        await ctx.message.delete()

    @discord.app_commands.command(name="verify")
    @discord.app_commands.guild_only()
    async def verify_command(
        self, interaction: discord.Interaction[ProjectHyperlink], roll: str
    ):
        verified = await checks._is_verified(interaction, True)
        if verified:
            raise UserAlreadyVerified

        await verify(self.bot, interaction, roll)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return

        async with self.bot.session.get(
            f"{config.API_URL}/students/{member.id}",
            headers={"Authorization": f"Bearer {config.API_TOKEN}"},
        ) as resp:
            if resp.status == 200:
                student_dict = (await resp.json())["data"]
            else:
                student_dict = {}

        student = Student(**student_dict) if student_dict else None

        if member.guild.id == NITKKR_GUILD_ID:
            self.bot.dispatch("member_join_nit", member, student)
        elif member.guild.id in self.club_guild_ids:
            self.bot.dispatch("member_join_club", member, student)
        elif member.guild.id in self.affiliate_guild_ids:
            self.bot.dispatch("member_join_affiliate", member, student)

    @commands.Cog.listener()
    async def on_member_join_nit(self, member: discord.Member, student: Student | None):
        guild = member.guild
        l10n = await self.bot.get_l10n(guild.id)

        channel = discord.utils.get(guild.text_channels, name="verify-here")
        if channel is None:
            self.bot.logger.critical(
                f"Verification channel not found for the guild `{guild.name}`!"
            )
            return

        if student and student.is_verified:
            await assign_student_roles(student, member.guild)
            self.bot.logger.info(
                f"{member.mention} was provided direct access to `{guild.name}`"
            )
            return

        prompt = await channel.send(
            l10n.format_value("verification-prompt", {"member": member.mention}),
        )
        self.bot.logger.info(
            f"Verification prompt sent to new user in `{guild.name}`",
            extra={"user": member},
        )

        try:
            await self.bot.wait_for(
                "user_verify",
                check=lambda user, _: user.discord_id == member.id,
                timeout=1200.0,
            )
        except asyncio.TimeoutError:
            pass
        await prompt.delete()

    @commands.Cog.listener()
    async def on_user_verify(self, student: Student, old_user_id: int | None):
        guild = self.bot.get_guild(NITKKR_GUILD_ID)
        assert guild is not None

        l10n = await self.bot.get_l10n(guild.id)
        await kick_old(guild, old_user_id, l10n)

        await assign_student_roles(student, guild)

        if student.clubs:
            self.bot.dispatch("club_member_change", student, old_user_id)

        self.bot.dispatch("affiliate_member_change", student, old_user_id)
