async def getWebhook(channel, user):
    for webhook in await channel.webhooks():
        if webhook.user == user:
            return webhook

    return await channel.create_webhook(name='Webhook')
