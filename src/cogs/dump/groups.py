import sqlite3

import discord
from discord.ext import commands
from tabulate import tabulate

import cogs.checks as checks
from utils.l10n import get_l10n
from utils.utils import get_group_roles


class Groups(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.groups: dict[str, dict] = {}

    async def cog_check(self, ctx) -> bool:
        self.l10n = await get_l10n(
            ctx.guild.id if ctx.guild else 0, "groups", self.bot.pool
        )
        return await checks.is_verified().predicate(ctx)

    def get_group(self, group_name):
        group = self.bot.pool.fetchrow(
            """
            SELECT
                *
            FROM
                groups
            WHERE
                name = $1
                OR alias = $1
            """,
            group_name,
        )
        if not group:
            raise commands.CheckFailure("GroupNotFound")
        self.groups[group.pop("name")] = group

    @commands.group(invoke_without_command=True)
    async def group(self, ctx):
        await ctx.send_help(ctx.command)

    @group.group(invoke_without_command=True)
    async def show(self, ctx, name: str):
        await ctx.send_help(ctx.command)

    @show.command()
    async def clubs(self, ctx):
        cursor = self.bot.c.execute(
            """select Name, Faculty_Advisor, Contact_Number,
                Server_Invite, Guest_Role from groups
                where Kind != "Technical Society"
            """
        )
        _clubs = cursor.fetchall()
        columns = cursor.description

        clubs = []
        invite_found = False
        for club in _clubs:
            invite = club[-2] if club[-1] else None
            if invite:
                invite_found = True
            clubs.append([*club[:-2], invite])

        if not invite_found:
            columns = columns[:-1]

        table = tabulate(clubs, [column[0] for column in columns], tablefmt="psql")
        print(table)
        embed = discord.Embed(
            description=f"```swift\n{table}```", color=discord.Color.blurple()
        )
        await ctx.send(f"```swift\n{table}```")

    @group.group()
    @checks.is_authorised()
    async def add(self, ctx, group: str):
        self.get_group(group)

    async def add_group_member(self, roll: int, discord_id: int, batch: int):
        """Add the student to a group and assign roles"""
        try:
            self.bot.pool.execute(
                "INSERT INTO group_member VALUES ($1, $2)", roll, group_name
            )
        except sqlite3.IntegrityError:
            print("Already exists in database!")

        main_server_ids = self.bot.pool.fetch(
            """select id FROM verified_server
                WHERE batch = 0 or batch = ?
            """,
            (batch,),
        ).fetchall()
        for guild_id in main_server_ids:
            guild = self.bot.get_guild(guild_id)
            member = guild.get_member(discord_id)
            if member:
                role = discord.utils.get(guild.roles, name=self.alias or self.name)
                await member.add_roles(role)

        server_id = self.bot.c.execute(
            "select discord_server from groups where name = ?", (self.name,)
        ).fetchone()

        guild = self.bot.get_guild(server_id)
        member = guild.get_member(discord_id)
        if not member:
            return

        year_role, guest_role = get_group_roles(self.bot.pool, batch, guild)
        if guest_role in member.roles:
            await member.remove_roles(guest_role)
        if year_role not in member.roles:
            await member.add_roles(year_role)

    @add.command()
    async def name(self, ctx, batch: int, *names: str):
        clashes = []
        unknown_records = []
        count = 0
        for name in names:
            records = self.bot.c.execute(
                """select Roll_Number, Discord_UID
                from main where Name like ? and Batch = ?""",
                (f"%{name}%", batch),
            ).fetchall()
            if len(records) > 1:
                clashes.append([name, *[record[0] for record in records]])
            elif not records:
                unknown_records.append(name)
            else:
                await self.add_group_member(records[0][0], records[0][1], batch)

        for clash in clashes:
            print(clash)
        print()
        for unknown_record in unknown_records:
            print(unknown_record)
        self.bot.db.commit()
        await ctx.reply(
            f"Added {len(names)} members to {self.alias or self.name} and added the role to {count} members"
        )

    @add.command()
    async def roll(self, ctx, roll_numbers: commands.Greedy[int]):
        unknown_records = []
        for roll in roll_numbers:
            id = self.bot.c.execute(
                "select Batch, Discord_UID from main where Roll_Number = ?", (roll,)
            ).fetchone()
            if not id:
                unknown_records.append(roll)
                continue

            await self.add_group_member(roll, id[1], id[0])

        for unknown_record in unknown_records:
            print(unknown_record)
        self.bot.db.commit()
        await ctx.reply(
            f"Added {len(roll_numbers) - len(unknown_records)} members to {self.alias or self.name}"
        )


async def setup(bot):
    await bot.add_cog(Groups(bot))
