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
