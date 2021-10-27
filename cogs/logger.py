from utils.l10n import get_l10n

import discord
from discord.ext import commands


class Logger(commands.Cog):
    """Logs edited and deleted messages"""

    def __init__(self, bot):
        self.bot = bot
        self.cache = {}

        guild_channels = bot.c.execute(
            'select ID, Edit_Channel, Delete_Channel from guilds'
        ).fetchall()
        for channels in guild_channels:
            edit = self.bot.get_channel(channels[1])
            delete = self.bot.get_channel(channels[2])
            self.cache[channels[0]] = edit, delete

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Called when a message is deleted"""
        if message.author.bot or not message.guild:
            return

        if message.guild.id not in self.cache:
            return

        l10n = get_l10n(message.guild.id, 'logger')

        embed = discord.Embed(
            description=l10n.format_value(
                'message-delete',
                {'channel': message.channel.mention}
            ),
            color=discord.Color.red()
        )
        embed.set_author(
            name=message.author, icon_url=message.author.display_avatar.url
        )
        embed.add_field(
            name=l10n.format_value('content'),
            value=message.content or l10n.format_value('content-notfound')
        )

        if message.attachments:
            if 'image' in message.attachments[0].content_type:
                embed.set_image(url=message.attachments[0].url)
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(
            text=l10n.format_value('user-id', {'id': message.author.id})
        )

        await self.cache[message.guild.id][1].send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent):
        """Called when multiple messages are deleted at once"""
        if payload.guild_id not in self.cache:
            return

        l10n = get_l10n(payload.guild_id, 'logger')

        messages = {
            'count': len(payload.message_ids),
            'channel': self.bot.get_channel(payload.channel_id).mention
        }

        embed = discord.Embed(
            description=l10n.format_value('messages-delete', messages),
            color=discord.Color.red()
        )
        embed.timestamp = discord.utils.utcnow()

        await self.cache[payload.guild_id][1].send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Called when a message is edited"""
        if before.author.bot or not before.guild:
            return

        if before.guild.id not in self.cache:
            return

        if before.content == after.content:
            return

        l10n = get_l10n(before.guild.id, 'logger')

        embed = discord.Embed(
            description=l10n.format_value(
                'message-edit',
                {'channel': before.channel.mention, 'url': before.jump_url}
            ),
            color=discord.Color.orange()
        )
        embed.set_author(
            name=before.author,
            icon_url=before.author.display_avatar.url
        )

        embed.add_field(
            name=l10n.format_value('message-old'),
            value=before.content or l10n.format_value('content-notfound')
        )
        embed.add_field(
            name=l10n.format_value('message-new'),
            value=after.content or l10n.format_value('content-notfound'),
            inline=False
        )
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(
            text=l10n.format_value('user-id', {'id': before.author.id})
        )

        await self.cache[before.guild.id][0].send(embed=embed)


def setup(bot):
    """Called when this file is attempted to be loaded as an extension"""
    bot.add_cog(Logger(bot))
