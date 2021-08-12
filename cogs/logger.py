import json

from datetime import datetime

from discord import Embed, Color
from discord.ext import commands

class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        with open('db/guilds.json') as f:
            guild_data = json.load(f)

        channel = self.bot.get_channel(guild_data[str(message.guild.id)]['logging_channel'][0])
        if not channel:
            return
        embed = Embed(
            description = f'Message deleted in {message.channel.mention}',
            color = Color.from_rgb(255, 0, 0)
        )
        embed.set_author(name=message.author, icon_url=message.author.avatar_url)
        if not message.content:
            embed.add_field(name='**Content**', value='Could not find message content')
        else:
            embed.add_field(name='**Content**', value=message.content)
        if message.attachments:
            if 'image' in message.attachments[0].content_type:
                embed.set_image(url=message.attachments[0].url)
        embed.timestamp = datetime.utcnow()
        embed.set_footer(text=f'User ID: {message.author.id}')
        try:
            await channel.send(embed=embed)
        except:
            print(message.content)

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload):
        with open('db/guilds.json') as f:
            guild_data = json.load(f)

        channel = self.bot.get_channel(guild_data[str(payload.guild_id)]['logging_channel'][0])
        if not channel:
            return

        embed = Embed(
            description = f'{len(payload.cached_messages)} messages were deleted in {payload.cached_messages[0].channel.mention}',
            color = Color.from_rgb(255, 0, 0)
        )
        embed.timestamp = datetime.utcnow()
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return

        with open('db/guilds.json') as f:
            guild_data = json.load(f)

        channel = self.bot.get_channel(guild_data[str(before.guild.id)]['logging_channel'][1])
        if not channel:
            return
        if before.content == after.content:
            return
        embed = Embed(
            description = f'Message edited in {before.channel.mention} - [Jump to message]({before.jump_url})',
            color = Color.from_rgb(255, 255, 0)
        )
        embed.set_author(name=before.author, icon_url=before.author.avatar_url)
        if not before.content:
            embed.add_field(name='**Old Message**', value='Could not find message content')
        else:
            embed.add_field(name='**Old Message**', value=before.content)
        if not after.content:
            embed.add_field(name='**New Message**', value='Could not find message content', inline=False)
        else:
            embed.add_field(name='**New Message**', value=after.content, inline=False)
        embed.timestamp = datetime.utcnow()
        embed.set_footer(text=f'User ID: {before.author.id}')
        try:
            await channel.send(embed=embed)
        except:
            print(before.content)

def setup(bot):
    bot.add_cog(Logger(bot))
