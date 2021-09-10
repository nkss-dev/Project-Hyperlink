async def deleteOnReaction(ctx, message, emoji: str='🗑️'):
    """deletes the given message when a certain reaction is used"""
    await message.add_reaction(emoji)

    def check(reaction, member):
        if reaction.emoji != emoji or member == ctx.guild.me:
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

async def getWebhook(channel, member):
    for webhook in await channel.webhooks():
        if webhook.user == member:
            return webhook
    if channel.permissions_for(member).manage_webhooks:
        webhook = await channel.create_webhook(
            name=member.name,
            avatar=await member.display_avatar.read()
        )
        return webhook
