async def getWebhook(channel, user):
    for webhook in await channel.webhooks():
        if webhook.user == user:
            return webhook
    webhook = await channel.create_webhook(
        name=user.name,
        avatar=await user.display_avatar.read()
    )
    return webhook
