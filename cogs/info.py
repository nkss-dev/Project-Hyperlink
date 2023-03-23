import json
from datetime import datetime
from typing import Optional

import config
import discord
from discord import app_commands
from discord.ext import commands
from tabulate import tabulate

from main import ProjectHyperlink
from models.courses import Course, Specifics
from utils import checks


class Info(commands.Cog):
    """Information commands"""

    def __init__(self, bot: ProjectHyperlink):
        self.bot = bot
        self.ctx_menu = app_commands.ContextMenu(
            name="Profile",
            callback=self.profile,
        )
        self.bot.tree.add_command(self.ctx_menu)

        with open("db/emojis.json") as f:
            self.emojis = json.load(f)["utility"]

    async def cog_load(self):
        async with self.bot.session.get(f"{config.api_url}/hostels") as resp:
            assert resp.status == 200
            data = await resp.json()
        self.hostels = {hostel.pop("id"): hostel for hostel in data["data"]}

    async def interaction_check(
        self, interaction: discord.Interaction[ProjectHyperlink], /
    ) -> bool:
        self.l10n = await self.bot.get_l10n(interaction.guild_id or 0)
        return super().interaction_check(interaction)

    @app_commands.command()
    @app_commands.describe(
        code="The code of the course that you want",
        only_content="A boolean if you only want to see the content of the course",
    )
    async def course(
        self, interaction: discord.Interaction, code: str, only_content: bool = True
    ):
        async with self.bot.session.get(f"{config.api_url}/courses/{code}") as resp:
            # TODO: Make a global fetcher util
            if resp.status != 200:
                raise app_commands.AppCommandError("UnhandledError")
            data = (await resp.json())["data"]

        specifics = [Specifics(**specific) for specific in data.pop("specifics")]
        course = Course(**data, specifics=specifics)

        embed = discord.Embed(color=interaction.user.color, title=course.title)
        if course.prereq:
            embed.add_field(
                name="Prerequisites",
                value=", ".join(
                    [
                        f"[{prereq}](https://nksss.live/courses/{prereq})"
                        for prereq in course.prereq
                    ]
                ),
            )
        embed.add_field(name="Type", value=course.kind)

        if only_content:
            for index, unit in enumerate(course.content, start=1):
                embed.add_field(
                    name=f"Unit {index}", value="```" + unit + "```", inline=False
                )
            await interaction.response.send_message(embed=embed)
            return

        embed.add_field(
            name="Objectives", value="• " + "\n• ".join(course.objectives), inline=False
        )
        embed.add_field(
            name="Outcomes", value="• " + "\n• ".join(course.outcomes), inline=False
        )
        embed.add_field(
            name="Reference Books",
            value="• " + "\n• ".join(course.book_names),
            inline=False,
        )
        content_embed = discord.Embed(
            color=interaction.user.color,
            title="Content",
        )
        await interaction.response.send_message(embeds=[embed, content_embed])

    async def get_profile_embed(self, guild: bool, member) -> discord.Embed:
        """Return the details of the given user in an embed"""
        async with self.bot.session.get(
            f"{config.api_url}/discord/users/{member.id}",
            headers={"Authorization": f"Bearer {config.api_token}"},
        ) as resp:
            if resp.status == 200:
                student = (await resp.json())["data"]
            else:
                return discord.Embed()

        # Set color based on context
        if guild and isinstance(member, discord.Member):
            color = member.color
        else:
            color = discord.Color.blurple()

        # Set emoji based on verification status
        status = "verified" if student["is_verified"] else "not-verified"

        # Generating the embed
        embed = discord.Embed(
            title=f"{student['name']} {self.emojis[status]}", color=color
        )
        embed.set_author(
            name=self.l10n.format_value("profile-name", {"member": str(member)}),
            icon_url=member.display_avatar.url,
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        # Add generic student details
        if hostel := student["hostel_id"]:
            hostel = f"{hostel} - {self.hostels[hostel]['name']}"

        fields = {
            "roll": student["roll_number"],
            "sec": student["section"],
            "email": student["email"],
            "hostel": hostel,
            "groups": ", ".join(student["clubs"].keys())
            or self.l10n.format_value("no-group"),
        }
        if student["mobile"]["Valid"]:
            fields["mob"] = student["mobile"]["String"]
        if student["birth_date"]["Valid"]:
            birth_date = datetime.strptime(
                student["birth_date"]["Time"][:10], "%Y-%m-%d"
            )
            fields["bday"] = discord.utils.format_dt(birth_date, style="D")

        for name, value in fields.items():
            embed.add_field(name=self.l10n.format_value(name), value=value)

        # Fetch member roles
        user_roles = []
        if guild:
            ignored_roles = [
                student["section"][:4],
                student["section"][:3] + student["section"][4:].zfill(2),
                student["hostel_id"],
                *student["clubs"].keys(),
                "@everyone",
            ]
            for role in member.roles:
                try:
                    ignored_roles.remove(role.name)
                except ValueError:
                    user_roles.append(role.mention)
            if user_roles:
                user_roles = ", ".join(user_roles[::-1])

        # Add field displaying the user's server/Discord join date
        if guild and user_roles:
            embed.add_field(name=self.l10n.format_value("roles"), value=user_roles)

        join_dt = member.joined_at if guild else member.created_at
        embed.add_field(
            name=self.l10n.format_value("join"),
            value=discord.utils.format_dt(join_dt, style="D"),
            inline=False,
        )

        return embed

    @checks.is_exists()
    async def profile(
        self, interaction: discord.Interaction, member: discord.Member | discord.User
    ):
        """View your or someone else's personal profile card."""
        """
        Parameters
        ------------
        `member`: Optional[Union[discord.Member, discord.User]]
            The member whose profile is displayed. If this is specified, \
            a check is performed to see if the author of the command is \
            authorised to view another user's profile. If left blank, the \
            member defaults to the author of the command.
        """
        if member.bot:
            raise app_commands.CheckFailure("NotForBot")

        if member != interaction.user:
            auth = await checks.is_authorised().predicate(interaction)
            if auth is False:
                await interaction.response.send_message(
                    self.l10n.format_value("MissingAuthorisation-profile"),
                    ephemeral=True,
                )
                return

        embed = await self.get_profile_embed(bool(interaction.guild), member)
        if not embed:
            raise app_commands.CheckFailure(
                "RecordNotFound", {"member": member.mention}
            )
        else:
            await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="profile")
    @app_commands.rename(member="user")
    @app_commands.describe(member="The user whose profile will be displayed")
    async def command_profile(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member | discord.User],
    ):
        await self.profile(interaction, member or interaction.user)

    # Deprecated command
    @app_commands.command()
    @checks.is_verified()
    @commands.bot_has_permissions(manage_nicknames=True)
    @app_commands.guild_only()
    async def nick(
        self, interaction: discord.Interaction, *, member: Optional[discord.Member]
    ):
        """Change your or someone else's nick to their first name."""
        """
        Parameters
        ------------
        `member`: Optional[discord.Member]
            The member whose nick is to be changed. If this is specified, \
            a check is performed to see if the author of the command is \
            authorised to change another user's nickname.
            If left blank, the member defaults to the author of the command.
        """
        member = member or interaction.user
        if member.id in config.owner_ids:
            pass
        elif member != interaction.user:
            if not interaction.user.guild_permissions.manage_nicknames:
                raise commands.MissingPermissions(["manage_nicknames"])
        else:
            if not member.guild_permissions.change_nickname:
                raise commands.MissingPermissions(["change_nickname"])

        name = await self.bot.pool.fetchval(
            "SELECT name FROM student WHERE discord_id = $1", member.id
        )

        if not name:
            # ctx.author = member
            raise commands.CheckFailure("RecordNotFound")

        old_nick = member.nick
        first_name = name.split(" ", 1)[0]
        await member.edit(nick=first_name)

        nick = {"member": member.mention, "old": f"{old_nick}", "new": first_name}
        embed = discord.Embed(
            description=self.l10n.format_value("nick-change-success", nick),
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    @app_commands.describe(batch="The batch of which the stats will be displayed")
    @checks.is_verified()
    async def memlist(self, interaction: discord.Interaction, batch: int):
        """View the stats of students of the specified batch.

        The displayed table has 3 value columns and is separated by sub-sections
        Columns:
            `Joined`: Represents users that have linked their Discord account \
                with a student's details in the database.
            `Remaining`: Represents users that have not linked their Discord \
                account with a student's details in the database.
            `Verified`: Represents users whose identities have been confirmed.
        """
        """
        Parameters
        ------------
        `batch`: <class 'int'>
            The batch for which the stats are shown.
        """
        data = await self.bot.pool.fetch(
            """
            SELECT
                section,
                COUNT(discord_id) AS joined,
                COUNT(*) - COUNT(discord_id) AS remaining,
                COUNT(*) FILTER (WHERE is_verified) AS verified
            FROM
                student
            WHERE
                batch = $1
            GROUP BY
                section
            ORDER BY
                section
            """,
            batch,
        )
        if not data:
            await interaction.response.send_message(
                self.l10n.format_value("NotFound-batch"), ephemeral=True
            )
            return

        sections, counts = [], []
        for row in data:
            if sections and row["section"][:4] == sections[-1]:
                count = counts[-1]
                counts[-1] = [
                    count[0] + row["joined"],
                    count[1] + row["remaining"],
                    count[2] + row["verified"],
                ]
            else:
                sections.append(row["section"][:4])
                counts.append([row["joined"], row["remaining"], row["verified"]])
        data = [[section, *count] for section, count in zip(sections, counts)]

        # Get the indices of the rows to be deleted
        indices = []
        previous = sections[0]
        for i, section in zip(range(2, len(sections) * 2, 2), sections[1:]):
            if section[:2] == previous[:2]:
                indices.append(i + 2)
            previous = section

        # Get total values for each numerical column
        total = [sum(count) for count in zip(*counts)]

        table = tabulate(
            [*data, ["Total", *total]],
            headers=("Section", "Joined", "Remaining", "Verified"),
            tablefmt="grid",
        ).split("\n")
        table[2] = table[0]

        # Delete the extra dashed lines
        cropped_table = []
        for i, row in enumerate(table):
            try:
                indices.remove(i)
            except ValueError:
                cropped_table.append(row)
        cropped_table = "\n".join(cropped_table)

        embed = discord.Embed(
            description=f"```swift\n{cropped_table}```", color=discord.Color.blurple()
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command()
    async def invite(self, interaction: discord.Interaction):
        """Grab the invite links of some Discord servers"""
        servers = (
            "NITKKR: https://discord.gg/r7eckfHjvy",
            "NITKKR'24: https://discord.gg/4eF7R6afqv",
            "NITKKR'25: https://discord.gg/C4s3f3zKpq",
        )
        misc_servers = (
            "eSP NITKKR: https://discord.gg/myCYvRHSvr",
            "kkr++: https://discord.gg/epaTW7tjYR",
        )

        perms = discord.Permissions.none()
        # General Permssions
        perms.view_audit_log = True
        perms.manage_roles = True
        perms.kick_members = True
        perms.manage_nicknames = True
        perms.manage_webhooks = True
        perms.read_messages = True
        perms.manage_events = True
        # Text Permissions
        perms.send_messages = True
        perms.send_messages_in_threads = True
        perms.manage_messages = True
        perms.use_external_emojis = True
        perms.add_reactions = True

        embed = discord.Embed(
            title=self.l10n.format_value("invite"),
            description=f"<{discord.utils.oauth_url(self.bot.user.id, permissions=perms)}>",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name=self.l10n.format_value("servers"),
            value="\n".join(servers),
        )
        embed.add_field(
            name=self.l10n.format_value("misc_servers"), value="\n".join(misc_servers)
        )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(Info(bot))
