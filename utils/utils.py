import re
from math import floor
from random import random
from typing import Union

import config
import discord
from discord.ext.commands import BotMissingPermissions


async def deleteOnReaction(ctx, message: discord.Message, emoji: str = "🗑️"):
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

    await ctx.bot.wait_for("reaction_add", check=check)
    await message.delete()
    if ctx.guild and ctx.guild.me.guild_permissions.manage_messages:
        await ctx.message.delete()


def generateID(
    IDs: tuple | None = None,
    length: int = 5,
    seed: str = "01234567890123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
) -> str:
    """Return an ID string.

    If `IDs` is provided, the returned ID will be unique.
    """
    if IDs is None:
        IDs = ()

    ID = ""
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


async def get_any_webhook(
    *,
    channel: Union[
        discord.ForumChannel,
        discord.StageChannel,
        discord.TextChannel,
        discord.VoiceChannel,
    ],
    member: discord.Member,
    reason: str | None = None,
) -> discord.Webhook:
    """Return the first webhook owned by a user for a channel"""
    if channel.permissions_for(member).manage_webhooks:
        raise BotMissingPermissions(["manage_webhooks"])

    for webhook in await channel.webhooks():
        if webhook.user == member:
            return webhook

    webhook = await channel.create_webhook(
        name=member.name,
        avatar=await member.display_avatar.read(),
        reason=reason,
    )
    return webhook


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
    reactions = (config.emojis["yes"], config.emojis["no"])

    for reaction in reactions:
        await message.add_reaction(reaction)

    def check(reaction, member):
        if str(reaction.emoji) not in reactions:
            return False
        if member == ctx.bot.user or member != ctx.author or reaction.message != message:
            return False
        return True

    reaction, _ = await ctx.bot.wait_for("reaction_add", check=check)
    await message.delete()
    return str(reaction.emoji) == reactions[0]
