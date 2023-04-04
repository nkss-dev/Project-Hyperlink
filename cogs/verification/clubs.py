import discord
from discord.ext import commands

from base.cog import HyperlinkCog
from cogs.verification.utils import assign_student_roles, kick_old
from models.clubs import ClubDiscord, parse_club_discord
from models.student import Student


class ClubVerification(HyperlinkCog):
    """The Great Wall of club servers"""

    async def cog_load(self) -> None:
        club_guild_dicts = await self.bot.pool.fetch(
            """
            SELECT
                club_name,
                guild_id,
                guest_role,
                member_role
            FROM
                club_discord
            """
        )
        self.club_guilds = [
            parse_club_discord(club_guild_dict) for club_guild_dict in club_guild_dicts
        ]
        return await super().cog_load()

    @commands.Cog.listener()
    async def on_member_join_club(
        self, member: discord.Member, student: Student | None
    ):
        """Triggered when a user joins a club's Discord server"""
        club_guild = discord.utils.get(self.club_guilds, guild_id=member.guild.id)
        assert club_guild is not None

        if student is None:
            self.bot.dispatch("club_guest_join", club_guild, member)
            return

        if club_guild.club_name in student.clubs:
            self.bot.dispatch("club_member_join", club_guild, member, student)
        else:
            self.bot.dispatch("club_guest_join", club_guild, member, student)

    @commands.Cog.listener()
    async def on_club_member_join(
        self,
        club_guild: ClubDiscord,
        member: discord.Member,
        student: Student,
    ):
        """Triggered when a club's member joins its Discord server"""
        guild = self.bot.get_guild(club_guild.guild_id)
        assert guild is not None

        # TODO: Add functionality to add post holder roles
        # Do this by shifting `member_role` to another table
        roles = []
        if (role_id := club_guild.member_role) is not None:
            role = guild.get_role(role_id)
            if role is None:
                self.bot.logger.error(
                    f"(table: club_discord) -> Member role {role_id} not found for {club_guild.club_name}"
                )
            else:
                roles.append(role)

        await assign_student_roles(student, guild, roles)

        if (role_id := club_guild.guest_role) is not None:
            role = guild.get_role(role_id)
            if role is None:
                self.bot.logger.error(
                    f"(table: club_discord) -> Guest role {role_id} not found for {club_guild.club_name}"
                )
            else:
                await member.remove_roles(role)

    @commands.Cog.listener()
    async def on_club_guest_join(
        self,
        club_guild: ClubDiscord,
        member: discord.Member,
        student: Student | None = None,
    ):
        """Triggered when a club's guest joins its Discord server"""
        roles = []
        if (role_id := club_guild.guest_role) is not None:
            role = member.guild.get_role(role_id)
            if role is None:
                self.bot.logger.error(
                    f"(table: club_discord) -> Guest role {role_id} not found for {club_guild.club_name}"
                )
            else:
                roles.append(role)

        if student is None:
            if roles:
                await member.add_roles(*roles)
            return

        await assign_student_roles(student, member.guild, roles, truncate=True)

    @commands.Cog.listener()
    async def on_club_member_change(self, student: Student, old_user_id: int | None):
        """Triggered when a student in one or more clubs verifies"""
        assert student.discord_id is not None

        for club_guild in self.club_guilds:
            guild = self.bot.get_guild(club_guild.guild_id)
            assert guild is not None

            l10n = await self.bot.get_l10n(guild.id)
            await kick_old(guild, old_user_id, l10n)

            member = guild.get_member(student.discord_id)
            if member is None:
                continue

            self.bot.dispatch("member_join_club", member, student)
