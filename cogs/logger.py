from utils.l10n import get_l10n

import discord
from discord.ext import commands

class Logger(commands.Cog):
    """Message related audit log"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """invoked when a message is deleted"""
        if message.author.bot or not message.guild:
            return

        channel_id = self.bot.guild_data[str(message.guild.id)]['log'][0]
        if not (channel := self.bot.get_channel(channel_id)):
            return

        l10n = get_l10n(message.guild.id, 'logger')

        embed = discord.Embed(
            description = l10n.format_value(
                'message-delete',
                {'channel': message.channel.mention}
            ),
            color = discord.Color.red()
        )
        embed.set_author(name=message.author, icon_url=message.author.avatar.url)
        embed.add_field(
            name = l10n.format_value('content'),
            value = message.content or l10n.format_value('content-notfound')
        )

        if message.attachments:
            if 'image' in message.attachments[0].content_type:
                embed.set_image(url=message.attachments[0].url)
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text=l10n.format_value('user-id', {'id': str(message.author.id)}))

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent):
        """invoked when multiple messages are deleted"""
        channel_id = self.bot.guild_data[str(payload.guild_id)]['log'][0]
        if not (channel := self.bot.get_channel(channel_id)):
            return

        l10n = get_l10n(payload.guild_id, 'logger')

        messages = {
            'count': str(len(payload.message_ids)),
            'channel': self.bot.get_channel(payload.channel_id).mention
        }

        embed = discord.Embed(
            description = l10n.format_value('messages-delete', messages),
            color = discord.Color.red()
        )
        embed.timestamp = discord.utils.utcnow()

        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """invoked when a message is edited"""
        if before.author.bot or not before.guild:
            return

        channel_id = self.bot.guild_data[str(before.guild.id)]['log'][1]
        if not (channel := self.bot.get_channel(channel_id)):
            return

        if before.content == after.content:
            return

        l10n = get_l10n(before.guild.id, 'logger')

        embed = discord.Embed(
            description = l10n.format_value(
                'message-edit',
                {'channel': before.channel.mention, 'url': before.jump_url}
            ),
            color = discord.Color.orange()
        )
        embed.set_author(name=before.author, icon_url=before.author.avatar.url)

        embed.add_field(
            name = l10n.format_value('message-old'),
            value = before.content or l10n.format_value('content-notfound')
        )
        embed.add_field(
            name = l10n.format_value('message-new'),
            value = after.content or l10n.format_value('content-notfound'),
            inline=False
        )
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text=l10n.format_value('user-id', {'id': str(before.author.id)}))

        await channel.send(embed=embed)

def setup(bot):
    """invoked when this file is attempted to be loaded as an extension"""
    bot.add_cog(Logger(bot))
