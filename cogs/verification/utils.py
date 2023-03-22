import re
import smtplib
from email.message import EmailMessage

import asyncpg
import config
import discord

from main import ProjectHyperlink
from utils.utils import generateID

GUILD_IDS = {
    904633974306005033: 0,
    783215699707166760: 2024,
    915517972594982942: 2025,
}


async def authenticate(
    roll: str,
    name: str,
    email: str,
    bot: ProjectHyperlink,
    author: discord.Member,
    channel_id: int,
    send_message,
) -> bool:
    """Authenticate a given Disord user by verification through email."""
    otp = generateID(seed="01234567890123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    # Creating the email
    msg = EmailMessage()
    msg["Subject"] = f"Verification of {author} in {author.guild}"
    msg["From"] = config.email
    msg["To"] = email

    variables = {
        "{$user}": name,
        "{$otp}": otp,
        "{$guild}": author.guild.name,
        "{$channel}": "https://discord.com/channels/"
        + f"{author.guild.id}/{channel_id}",
    }
    with open("utils/verification.html") as f:
        html = f.read()
    html = re.sub(r"({\$\w+})", lambda x: variables[x.group(0)], html)
    msg.set_content(html, subtype="html")

    # Sending the email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(config.email, config.password_token)
        smtp.send_message(msg)

    def check(msg: discord.Message):
        return msg.author == author and msg.channel.id == channel_id

    while True:
        message: discord.Message = await bot.wait_for("message", check=check)
        content = message.content
        if otp == content:
            break

        await send_message(
            f"`{content}` is incorrent. Please try again with the correct OTP."
        )

    old_user_id = await bot.pool.fetchval(
        "SELECT discord_id FROM student WHERE roll_number = $1", roll
    )

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
        author.id,
        roll,
    )

    # TODO: Kick old account from affiliated servers

    return True


async def post_verification_handler(
    member: discord.Member, student: dict[str, str], conn: asyncpg.Pool
):
    """Do post successful verification stuff"""
    groups = await conn.fetch(
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
    interaction: discord.Interaction,
    member: discord.Member,
    roll: str,
):
    assert interaction.channel_id is not None

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

    await interaction.response.send_message(
        l10n.format_value("email-sent", {"email": student["email"]}),
        ephemeral=True,
    )

    verified = await authenticate(
        roll,
        student["name"],
        student["email"],
        bot,
        member,
        interaction.channel_id,
        interaction.followup.send,
    )
    if verified is False:
        return

    await interaction.followup.send(
        l10n.format_value("verification-success", {"mention": member.mention})
    )

    await post_verification_handler(member, student, bot.pool)
