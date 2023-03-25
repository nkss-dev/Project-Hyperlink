import asyncio
import re
import smtplib
from email.message import EmailMessage
from typing import TYPE_CHECKING

import config
import discord
from fluent.runtime import FluentLocalization

from . import GUILD_IDS
from cogs.errors.app import IncorrectGuildBatch, OTPTimeout, RollNotFound
from models.student import Student, parse_student
from utils.utils import generateID

if TYPE_CHECKING:
    from main import ProjectHyperlink
else:
    ProjectHyperlink = discord.ext.commands.Bot


async def assign_student_roles(
    student: Student,
    guild: discord.Guild,
    extra_roles: list[discord.Role] | None = None,
    *,
    truncate: bool = False,
):
    role_names = (
        student.section[:2],
        student.section[:4],
        student.section[:3] + student.section[4:].zfill(2),
        student.batch,
        student.hostel_id,
        *student.clubs.keys(),
        "verified",
    )

    assert student.discord_id is not None
    member = guild.get_member(student.discord_id)
    if member is None:
        return

    roles = []
    for role_name in role_names:
        if role := discord.utils.get(member.guild.roles, name=str(role_name)):
            roles.append(role)
    if extra_roles is not None:
        roles.extend(extra_roles)

    if truncate:
        await member.edit(roles=roles)
    else:
        await member.add_roles(*roles)

    if member.display_name != student.name:
        first_name = student.name.split(" ", 1)[0]
        try:
            await member.edit(nick=first_name)
        except discord.Forbidden:
            pass


async def authenticate(
    name: str,
    email: str,
    bot: ProjectHyperlink,
    member: discord.Member,
    interaction: discord.Interaction[ProjectHyperlink],
    l10n: FluentLocalization,
) -> bool:
    """Authenticate a given Disord user by verification through email."""
    await interaction.response.send_message(
        l10n.format_value("email-sent", {"email": email}),
        ephemeral=True,
    )

    otp = generateID(seed="01234567890123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    # Creating the email
    msg = EmailMessage()
    msg["Subject"] = f"Verification of {member} in {member.guild}"
    msg["From"] = config.email
    msg["To"] = email

    variables = {
        "{$user}": name,
        "{$otp}": otp,
        "{$guild}": member.guild.name,
        "{$channel}": "https://discord.com/channels/"
        + f"{member.guild.id}/{interaction.channel_id}",
    }

    # TODO: Parse HTML using html.parser.HTML instead of RegEx
    with open("utils/verification.html") as f:
        html = f.read()
    html = re.sub(r"({\$\w+})", lambda x: variables[x.group(0)], html)
    msg.set_content(html, subtype="html")

    # Sending the email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(config.email, config.password_token)
        smtp.send_message(msg)

    bot.logger.info(f"Verification email sent to `{email}`", extra={"user": member})

    def check(msg: discord.Message):
        return msg.author == member and msg.channel.id == interaction.channel_id

    while True:
        try:
            message: discord.Message = await bot.wait_for(
                "message", timeout=300.0, check=check
            )
        except asyncio.TimeoutError:
            bot.logger.warning(
                f"Verification timed out in `{member.guild.name}`",
                extra={"user": member},
            )
            raise OTPTimeout(member=member)
        else:
            await message.delete()

            temp_otp = message.content
            if otp == temp_otp:
                break

            await interaction.followup.send(
                l10n.format_value("BadRequest-otp", {"OTP": temp_otp}),
                ephemeral=True,
            )
            bot.logger.info(
                f"Incorrect OTP (`{temp_otp}`) provided for verification",
                extra={"user": member},
            )

    return True


async def verify(
    bot: ProjectHyperlink,
    interaction: discord.Interaction[ProjectHyperlink],
    roll: str,
):
    assert interaction.channel_id is not None
    assert isinstance(interaction.user, discord.Member)

    member = interaction.user

    l10n = await bot.get_l10n(interaction.guild.id if interaction.guild else 0)

    async with bot.session.get(
        f"{config.api_url}/students/{roll}",
        headers={"Authorization": f"Bearer {config.api_token}"},
    ) as resp:
        if resp.status == 200:
            student_dict = (await resp.json())["data"]
        else:
            raise RollNotFound(roll_number=roll)

    student = parse_student(student_dict)

    if GUILD_IDS[member.guild.id] != 0 and GUILD_IDS[member.guild.id] != student.batch:
        raise IncorrectGuildBatch(
            roll_number=student.roll_number,
            server_batch=GUILD_IDS[member.guild.id],
            student_batch=student.batch,
        )

    verified = await authenticate(
        student.name, student.email, bot, member, interaction, l10n
    )
    if verified is False:
        return

    await interaction.followup.send(
        l10n.format_value("verification-success", {"mention": member.mention}),
        ephemeral=True,
    )
    bot.logger.info(
        f"Verification successful in `{member.guild.name}`",
        extra={"user": member},
    )

    old_user_id = await bot.pool.fetchval(
        "SELECT discord_id FROM student WHERE roll_number = $1",
        student.roll_number,
    )
    # TODO: Kick `old_user_id` from affiliated servers

    student.discord_id = member.id
    await bot.pool.execute(
        """
        UPDATE
            student
        SET
            discord_id = $1,
            is_verified = true
        WHERE
            roll_number = $2
        """,
        student.discord_id,
        student.roll_number,
    )

    bot.dispatch("user_verify", student)
