import asyncio
import json

from re import fullmatch
from utils.l10n import get_l10n

import discord
from discord.ext import commands
from discord.utils import sleep_until

from datetime import datetime, timedelta
from typing import Union

class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_check(self, ctx):
        self.l10n = get_l10n(ctx.guild.id, 'mod')
        return self.bot.moderatorCheck(ctx)

    @commands.command(brief='Mutes user/role from the server/channel')
    async def mute(self, ctx, item: Union[discord.Member, discord.Role], duration, channel: discord.TextChannel=None):
        if not fullmatch('^(\d+:)?(([0-1]\d)|(2[0-4])):[0-6]\d$', duration):
            await ctx.reply(self.l10n.format_value('duration-incorrect-format'))
            return

        duration = list(map(int, duration.split(':')))
        days, hours, minutes = duration if len(duration) == 3 else [0, *duration]
        unmute_time = datetime.utcnow() + timedelta(days=days, hours=hours, minutes=minutes)

        if channel:
            overwrite = channel.overwrites_for(item)
            original_perm = overwrite.send_messages
            overwrite.send_messages = False
            await channel.set_permissions(item, overwrite=overwrite)

            await asyncio.sleep(1)
            if channel.permissions_for(item).send_messages:
                await ctx.reply(self.l10n.format_value('mute-ineffective', {'item': item.mention}))
            else:
                await ctx.reply(self.l10n.format_value('mute-effective', {'item': item.mention, 'place': channel.mention}))

            await sleep_until(unmute_time)

            overwrite = channel.overwrites_for(item)
            overwrite.send_messages = original_perm
            await channel.set_permissions(item, overwrite=overwrite)

        else:
            if isinstance(item, discord.Member):
                mute_role_id = self.bot.guild_data[str(ctx.guild.id)]['roles']['mute']
                if not (mute_role := ctx.guild.get_role(mute_role_id)):
                    await ctx.reply(self.l10n.format_value('mute-role-notfound'))
                    return

                await item.add_roles(mute_role)

                await ctx.reply(self.l10n.format_value('mute-effective', {'item': item.mention, 'place': guild.name}))

                await sleep_until(unmute_time)
                await item.remove_roles(mute_role)
            else:
                await ctx.reply(self.l10n.format_value('mute-role-not-allowed'))

def setup(bot):
    bot.add_cog(Mod(bot))
