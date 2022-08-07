import json
import re
from datetime import datetime
from math import floor
from random import random

import discord


async def assign_student_roles(member, details, conn):
    """Add multiple college related roles to the user.

    These currently include:
        Branch, Section, Sub-Section, Hostel, Clubs
    """
    groups = await conn.fetch(
        '''
        SELECT
            name,
            alias
        FROM
            club_discord_user
        WHERE
            discord_id = $1
        ''', member.id
    )

    role_names = (
        *details,
        *[group['alias'] or group['name'] for group in groups]
    )
    roles = []
    for role_name in role_names:
        if role := discord.utils.get(member.guild.roles, name=str(role_name)):
            roles.append(role)
    await member.add_roles(*roles)


async def deleteOnReaction(ctx, message: discord.Message, emoji: str = '🗑️'):
    """Delete the given message when a certain reaction is used"""
    await message.add_reaction(emoji)

    def check(reaction, member):
        if str(reaction.emoji) != emoji or member == ctx.bot.user:
            return False
        if member != ctx.author and not member.guild_permissions.manage_messages:
            return False
        if reaction.message != message:
            return False
        return True

    await ctx.bot.wait_for('reaction_add', check=check)
    await message.delete()
    if ctx.guild and ctx.guild.me.guild_permissions.manage_messages:
        await ctx.message.delete()


def generateID(IDs: tuple = None, length: int = 5, seed: str = None) -> str:
    """Return an ID string.

    If `IDs` is provided, the returned ID will be unique.
    """
    if IDs is None:
        IDs = ()

    seed = seed or '01234567890123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    ID = ''
    for _ in range(length):
        ID += seed[floor(random() * len(seed))]
    if ID in IDs:
        return generateID(IDs)
    return ID


def getURLs(text: str) -> list:
    if text is None:
        return []
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    return [url[0] for url in re.findall(regex, text)]


async def getWebhook(channel, member) -> discord.Webhook | None:
    """Return a webhook"""
    for webhook in await channel.webhooks():
        if webhook.user == member:
            return webhook
    if channel.permissions_for(member).manage_webhooks:
        webhook = await channel.create_webhook(
            name=member.name,
            avatar=await member.display_avatar.read()
        )
        return webhook


async def get_group_roles(conn, batch, guild) -> tuple[discord.Role, discord.Role] | None:
    names = {
        1: 'freshman',
        2: 'sophomore',
        3: 'junior',
        4: 'senior'
    }

    if batch:
        # Calculate which year the student is in
        passing_date = datetime(year=batch, month=6, day=1)
        time = passing_date - datetime.utcnow()
        remaining_years = time.days // 365
        year = names[4 - remaining_years]
    else:
        # Assigning temporary year for non-verified user
        year = names[1]

    # Fetch roles to be assigned
    roles = await conn.fetchrow(
        f'''
        SELECT
            {year}_role,
            guest_role
        FROM
            club_discord
        WHERE
            guild_id = $1
        ''', guild.id
    )
    if not roles:
        return None

    return (
        guild.get_role(roles[f'{year}_role']),
        guild.get_role(roles['guest_role'])
    )


async def is_alone(channel, author, bot) -> bool:
    alone = True
    if isinstance(channel, discord.DMChannel):
        return alone

    guild = channel.guild
    ids = author.id, bot.id
    if isinstance(channel, (discord.TextChannel, discord.Thread)):
        if isinstance(channel, discord.Thread):
            for user in await channel.fetch_members():
                member = guild.get_member(user.id)
                if not member.public_flags.verified_bot and member.id not in ids:
                    alone = False
                    break
        else:
            for member in channel.members:
                if not member.public_flags.verified_bot and member.id not in ids:
                    alone = False
                    break

    return alone


async def yesOrNo(ctx, message: discord.Message) -> bool:
    """Return true or false based on the user's reaction"""
    with open('db/emojis.json') as f:
        emojis = json.load(f)['utility']
    reactions = (emojis['yes'], emojis['no'])

    for reaction in reactions:
        await message.add_reaction(reaction)

    def check(reaction, member):
        if str(reaction.emoji) not in reactions:
            return False
        if member == ctx.bot.user or member != ctx.author or reaction.message != message:
            return False
        return True

    reaction, _ = await ctx.bot.wait_for('reaction_add', check=check)
    await message.delete()
    return str(reaction.emoji) == reactions[0]
