import discord
import json

async def deleteOnReaction(ctx, message: discord.Message, emoji: str='🗑️'):
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

async def getWebhook(channel: discord.TextChannel, member: discord.Member):
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
