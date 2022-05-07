from utils.l10n import get_l10n

import discord
from discord.ext import commands


class Logger(commands.Cog):
    """Logs edited and deleted messages"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.channel_ids: dict[int, tuple[int, int]] = {}

    async def cog_load(self):
        guild_channels = await self.bot.conn.fetch(
            'SELECT id, edit_channel, delete_channel FROM guild'
        )
        for channels in guild_channels:
            edit = channels['edit_channel']
            delete = channels['delete_channel']
            self.channel_ids[channels['id']] = edit, delete

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Called when a message is deleted"""
        if message.author.bot or not message.guild:
            return

        if message.guild.id not in self.channel_ids:
            return

        l10n = await get_l10n(message.guild.id, 'logger', self.bot.conn)

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

        channel = self.bot.get_channel(self.channel_ids[message.guild.id][1])
        if not channel:
            # Placeholder for error logging system
            return
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent):
        """Called when multiple messages are deleted at once"""
        if payload.guild_id not in self.channel_ids:
            return

        l10n = await get_l10n(payload.guild_id, 'logger', self.bot.conn)

        messages = {
            'count': len(payload.message_ids),
            'channel': self.bot.get_channel(payload.channel_id).mention
        }

        embed = discord.Embed(
            description=l10n.format_value('messages-delete', messages),
            color=discord.Color.red()
        )
        embed.timestamp = discord.utils.utcnow()

        channel = self.bot.get_channel(self.channel_ids[payload.guild_id][1])
        if not channel:
            # Placeholder for error logging system
            return
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Called when a message is edited"""
        if before.author.bot or not before.guild:
            return

        if before.guild.id not in self.channel_ids:
            return

        if before.content == after.content:
            return

        l10n = await get_l10n(before.guild.id, 'logger', self.bot.conn)

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

        channel = self.bot.get_channel(self.channel_ids[before.guild.id][0])
        if not channel:
            # Placeholder for error logging system
            return
        await channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Logger(bot))
