import asyncio
import re
import smtplib
from email.message import EmailMessage

import asyncpg
import config
import discord
from fluent.runtime import FluentLocalization

from main import ProjectHyperlink
from utils.utils import generateID

GUILD_IDS = {
    904633974306005033: 0,
    783215699707166760: 2024,
    915517972594982942: 2025,
}


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
            raise discord.app_commands.CheckFailure(
                "TimeoutError-otp", {"author": member.mention}
            )
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


async def post_verification_handler(
    member: discord.Member, student: dict[str, str], pool: asyncpg.Pool
):
    """Do post successful verification stuff"""
    old_user_id = await pool.fetchval(
        "SELECT discord_id FROM student WHERE roll_number = $1",
        student["roll_number"],
    )

    await pool.execute(
        """
        UPDATE
            student
        SET
            discord_id = $1,
            is_verified = true
        WHERE
            roll_number = $2
        """,
        member.id,
        student["roll_number"],
    )

    # TODO: Kick `old_user_id` from affiliated servers

    groups = await pool.fetch(
        """
        SELECT
            COALESCE(club.alias, club.name) AS short_name
        FROM
            club
        WHERE
            club.name = ANY(SELECT club_name FROM club_member WHERE roll_number = $1)
        """,
        student["roll_number"],
    )

    role_names = (
        student["section"][:2],
        student["section"][:4],
        student["section"][:3] + student["section"][4:].zfill(2),
        student["batch"],
        student["hostel_id"],
        *[group["short_name"] for group in groups],
        "verified",
    )
    roles = []
    for role_name in role_names:
        if role := discord.utils.get(member.guild.roles, name=str(role_name)):
            roles.append(role)
    await member.add_roles(*roles)

    if member.display_name != student["name"]:
        first_name = student["name"].split(" ", 1)[0]
        await member.edit(nick=first_name)

    # TODO: Allow access to the user in all other affiliated guilds


async def verify(
    bot: ProjectHyperlink,
    interaction: discord.Interaction[ProjectHyperlink],
    roll: str,
):
    assert interaction.channel_id is not None
    assert isinstance(interaction.user, discord.Member)

    member = interaction.user

    l10n = await bot.get_l10n(interaction.guild.id if interaction.guild else 0)

    student: dict[str, str] = await bot.pool.fetchrow(
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
            roll_number = $1
        """,
        roll,
    )
    if not student:
        raise discord.app_commands.CheckFailure("NotFound-roll", {"roll": roll})

    if (
        GUILD_IDS[member.guild.id] != 0
        and GUILD_IDS[member.guild.id] != student["batch"]
    ):
        raise discord.app_commands.CheckFailure(
            "BadRequest-restricted-guild",
            {
                "roll": student["roll_number"],
                "server_batch": GUILD_IDS[member.guild.id],
                "student_batch": student["batch"],
            },
        )

    verified = await authenticate(
        student["name"], student["email"], bot, member, interaction, l10n
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

    await post_verification_handler(member, student, bot.pool)
