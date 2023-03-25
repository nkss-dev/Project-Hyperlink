import config
import discord
from discord.ext import commands

from main import ProjectHyperlink
from models.clubs import parse_club_discord
from models.student import parse_student


class Club(commands.Cog):
    def __init__(self, bot: ProjectHyperlink):
        self.bot = bot

    async def cog_load(self) -> None:
        club_discord_dicts = await self.bot.pool.fetch(
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
        self.club_discord = [
            parse_club_discord(club_discord_dict)
            for club_discord_dict in club_discord_dicts
        ]
        return await super().cog_load()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        club_discord = discord.utils.get(self.club_discord, guild_id=member.guild.id)
        if club_discord is None:
            return

        async with self.bot.session.get(
            f"{config.api_url}/discord/users/{member.id}",
            headers={"Authorization": f"Bearer {config.api_token}"},
        ) as resp:
            if resp.status == 200:
                student_dict = (await resp.json())["data"]
            else:
                student_dict = {}

        if student_dict:
            student = parse_student(student_dict)
            self.bot.dispatch("user_verify", student, member.guild.id)

            # TODO: Add functionality to add post holder roles
            # Do this by shifting `member_role` to another table
            if club_discord.club_name in student.clubs:
                role_id = club_discord.member_role
            else:
                role_id = club_discord.guest_role

        else:
            role_id = club_discord.guest_role

        if role_id is None:
            self.bot.logger.warning(
                f"(table: club_discord) -> Neither guest nor member role found"
            )
            return

        role = member.guild.get_role(role_id)
        if role is None:
            self.bot.logger.error(
                f"(table: club_discord) -> Role ID {role_id} not found for {club_discord.club_name}"
            )
            return

        await member.add_roles(role)


async def setup(bot: ProjectHyperlink):
    await bot.add_cog(Club(bot))
