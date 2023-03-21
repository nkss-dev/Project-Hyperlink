import contextlib
import json
import re
from asyncio import TimeoutError
from dataclasses import dataclass
from typing import Optional

import config
import discord
from discord.ext import commands
import smtplib
from email.message import EmailMessage
from main import ProjectHyperlink

from utils import checks
from utils.utils import assign_student_roles, generateID


@dataclass
class BasicInfo:
    branch: Optional[str]
    section: Optional[str]
    roll: Optional[int]


def parse_verify_basic(params: str) -> BasicInfo:
    roll = None
    branch = None
    section = None

    if roll := re.search(r"\d{4,}", params):
        roll = int(roll.group(0))

    # try XY-A or XY-A2
    if section_name := re.search(r"([A-Z]{2})[- ]?([ABC]\d{1,2})?", params, re.I):
        branch = section_name.group(1)
        section = section_name.group(2)

    return BasicInfo(branch, section, roll)


class Verify(commands.Cog):
    """DEPRECATED: Verification management"""

    def __init__(self, bot: ProjectHyperlink):
        self.bot = bot

        with open("db/emojis.json") as emojis:
            self.emojis = json.load(emojis)["utility"]

    async def cog_load(self):
        sections = await self.bot.pool.fetch(
            """
            SELECT
                batch,
                ARRAY_AGG(DISTINCT section)
            FROM
                student
            GROUP BY
                batch
        """
        )
        self.sections = dict(sections)

        ids = await self.bot.pool.fetch(
            """
            SELECT
                guild_id
            FROM
                affiliated_guild
            UNION
            SELECT
                guild_id
            FROM
                club_discord
        """
        )
        self.guild_ids = [id["guild_id"] for id in ids]

    async def authenticate(
        self, ctx, roll: int, name: str, email: str, new_user: bool = True
    ) -> bool:
        """Authenticate a given Disord user by verification through email."""
        otp = generateID(seed="01234567890123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")

        # Creating the email
        msg = EmailMessage()
        msg["Subject"] = f"Verification of {ctx.author} in {ctx.guild}"
        msg["From"] = config.email
        msg["To"] = email

        variables = {
            "{$user}": name,
            "{$otp}": otp,
            "{$guild}": ctx.guild.name,
            "{$channel}": "https://discord.com/channels/"
            + f"{ctx.guild.id}/{ctx.channel.id}",
        }
        with open("utils/verification.html") as f:
            html = f.read()
        html = re.sub(r"({\$\w+})", lambda x: variables[x.group(0)], html)
        msg.set_content(html, subtype="html")

        # Sending the email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(config.email, config.password_token)
            smtp.send_message(msg)

        def check(msg):
            return msg.author == ctx.author and msg.channel == ctx.channel

        while True:
            try:
                ctx.message = await self.bot.wait_for(
                    "message", timeout=240.0, check=check
                )
            except TimeoutError:
                await ctx.send(self.fmv("verification-timeout"))
                return False
            else:
                content = ctx.message.content
                if otp == content:
                    break

                await ctx.reply(self.fmv("otp-retry", {"otp": content}))

        # Fetch the user ID again in case another
        # account has verified in the meantime
        old_user_id = await self.bot.pool.fetchval(
            "SELECT discord_id FROM student WHERE roll_number = $1", str(roll)
        )

        if new_user:
            await self.bot.pool.execute(
                """
                UPDATE
                    student
                SET
                    discord_id = $1,
                    is_verified = true
                WHERE
                    roll_number = $2
                """,
                ctx.author.id,
                str(roll),
            )
        else:
            await self.bot.pool.execute(
                "UPDATE student SET is_verified = true WHERE roll_number = $1",
                str(roll),
            )

        # Kick the old account from all affiliated servers, if any
        for id in self.guild_ids:
            guild = self.bot.get_guild(id)
            member = guild.get_member(old_user_id)
            if not member:
                continue

            with contextlib.suppress(discord.Forbidden):
                await member.kick(
                    reason=self.fmv("member-kick", {"user": ctx.author.mention})
                )

        return True

    async def cleanup(self, author, name):
        """Post-successful-verification stuff"""
        guild = author.guild

        # Remove restricting role
        id = await self.bot.pool.fetchval(
            "SELECT guest_role FROM affiliated_guild WHERE guild_id = $1", guild.id
        )
        if guest_role := guild.get_role(id):
            await author.remove_roles(guest_role)

        # Add nickname
        if author.display_name != name:
            first_name = name.split(" ", 1)[0]
            await author.edit(nick=first_name)

    @commands.group()
    @commands.guild_only()
    async def verify(self, ctx: commands.Context):
        """Command group for verification functionality"""
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)
            return

        self.guild_batch = await self.bot.pool.fetchval(
            "SELECT batch FROM affiliated_guild WHERE guild_id = $1", ctx.guild.id
        )
        if self.guild_batch is None:
            raise commands.CheckFailure("RestrictedGuild")

        if await checks.is_verified(True).predicate(ctx):
            raise commands.CheckFailure("UserAlreadyVerified")
        if ctx.invoked_subcommand.name == "basic":
            if ctx.guild.id == 904633974306005033:
                raise commands.CheckFailure("BasicVerificationNotAllowed")
            if await checks.is_exists(True).predicate(ctx):
                raise commands.CheckFailure("AccountAlreadyLinked")
        elif not await checks.is_exists(True).predicate(ctx):
            if ctx.guild.id != 904633974306005033:
                raise commands.CheckFailure("AccountNotLinked")

        l10n = await self.bot.get_l10n(ctx.guild.id)
        self.fmv = l10n.format_value

    @verify.command()
    @commands.max_concurrency(1, commands.BucketType.member)
    async def basic(self, ctx, *, params: str):
        """Allows you to access various bot functions and server channels.

        Type `verify basic` followed by your branch and section, like \
        `CS-A2`, followed by your roll number.

        Example: `%verify basic CS-B5 12022005`
        """
        """
        Parameters
        ------------
        `section`: <class 'str'>
            The section the student is in. Must match the following format:
                XY-Z
            where `XY` is the acronym for the branch and `Z` is the section.

        `roll`: <class 'int'>
            The roll number of the student.
        """
        info = parse_verify_basic(params)

        if info.roll is None:
            await ctx.reply(self.fmv("rollno-not-provided"))
            return

        if info.branch is None:
            await ctx.reply(self.fmv("branch-not-provided"))
            return

        if info.section is None:
            await ctx.reply(self.fmv("section-not-provided"))
            return

        roll = info.roll
        section = f"{info.branch}-{info.section}".upper()

        student = await self.bot.pool.fetchrow(
            """
            SELECT
                section,
                name,
                email,
                batch,
                hostel_id,
                discord_id
            FROM
                student
            WHERE
                roll_number = $1
            """,
            str(roll),
        )

        if not student:
            await ctx.reply(self.fmv("roll-not-in-database"))
            return

        if student["batch"] != self.guild_batch:
            await ctx.reply(self.fmv("incorrect-guild", {"batch": student["batch"]}))
            return

        if section not in self.sections[student["batch"]]:
            await ctx.reply(self.fmv("section-notfound", {"section": section}))
            return

        if section != student["section"]:
            await ctx.reply(self.fmv("section-mismatch"))
            return

        if student["discord_id"] and student["discord_id"] != ctx.author.id:
            await ctx.reply(self.fmv("email-sent", {"email": student["email"]}))

            authenticated = await self.authenticate(
                ctx, roll, student["name"], student["email"]
            )
            if not authenticated:
                return

        await ctx.reply(self.fmv("basic-success"))
        await assign_student_roles(
            ctx.author,
            (
                student["section"][:4],
                student["section"][:3] + student["section"][4:].zfill(2),
                student["hostel_id"],
            ),
            self.bot.pool,
        )

        await self.cleanup(ctx.author, student["name"])

    @verify.command()
    @commands.max_concurrency(1, commands.BucketType.member)
    async def email(self, ctx, email: str):
        """Type this command to prove your identity for more accessibility.

        Type `verify email` followed by your institute email, like \
        `email@nitkkr.ac.in`

        Example: `%verify email priyanshu_12022005@nitkkr.ac.in`
        """
        """
        Parameters
        ------------
        `email`: <class 'str'>
            The institute email of the user.
        """
        email = email.lower()
        new_user = not await checks.is_exists(True).predicate(ctx)

        if new_user:
            col, var = "email", email
        else:
            col, var = "discord_id", ctx.author.id
        student = await self.bot.pool.fetchrow(
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
                {col} = $1
            """,
            var,
        )
        if not student:
            await ctx.reply(self.fmv("email-notfound", {"email": email}))
            return
        if email != student["email"]:
            await ctx.reply(self.fmv("email-mismatch"))
            return

        await ctx.reply(self.fmv("email-sent", {"email": email}))

        authenticated = await self.authenticate(
            ctx, student["roll_number"], student["name"], email, new_user
        )
        if not authenticated:
            return

        await ctx.reply(self.fmv("email-success", {"emoji": self.emojis["verified"]}))
        await assign_student_roles(
            ctx.author,
            (
                student["section"][:2],
                student["section"][:4],
                student["section"][:3] + student["section"][4:].zfill(2),
                student["batch"],
                student["hostel_id"],
            ),
            self.bot.pool,
        )
        await self.cleanup(ctx.author, student["name"])


async def setup(bot):
    await bot.add_cog(Verify(bot))
