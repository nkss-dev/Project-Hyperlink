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
    """Moderator-only commands"""

    def __init__(self, bot):
        self.bot = bot

        with open('db/muted.json') as muted:
            self.muted = json.load(muted)

        self.bot.loop.create_task(self.loadAllMuted())

    def cog_check(self, ctx) -> bool:
        if not ctx.guild:
            raise commands.NoPrivateMessage
        self.l10n = get_l10n(ctx.guild.id, 'mod')
        return self.bot.moderatorCheck(ctx)

    @commands.command(aliases=['m'])
    async def mute(self, ctx, item: Union[discord.Member, discord.Role], duration: str, channel: discord.TextChannel = None):
        """Mute user/role from the server or a single channel.

        Parameters
        ------------
        `item`: Union[discord.Member, discord.Role]
            The member or role to be muted.

        `duration`: <class 'str'>
            The duration for which the member/role has to be muted.
            The format for this paramter is either `DD:HH:MM` or `HH:MM`

        `channel`: discord.TextChannel
            The channel in which the member/role has to be muted. If left \
            blank, this defaults to the entire server. Note that muting in \
            the entire server works only for a member and only if a mute role exists.
        """
        if not fullmatch('^(\d+:)?(([0-1]\d)|(2[0-4])):[0-6]\d$', duration):
            await ctx.reply(self.l10n.format_value('duration-incorrect-format'))
            return

        duration = list(map(int, duration.split(':')))
        days, hours, minutes = duration if len(duration) == 3 else [0, *duration]
        unmute_time = datetime.now() + timedelta(days=days, hours=hours, minutes=minutes)

        if channel:
            overwrite = channel.overwrites_for(item)
            original_perm = overwrite.send_messages
            overwrite.send_messages = False
            await channel.set_permissions(item, overwrite=overwrite)

            await asyncio.sleep(1)
            if channel.permissions_for(item).send_messages:
                embed = discord.Embed(
                    description=self.l10n.format_value(
                        'mute-ineffective',
                        {'item': item.mention}
                    ),
                    color=discord.Color.blurple()
                )
                await ctx.reply(embed=embed)
            else:
                embed = discord.Embed(
                    description=self.l10n.format_value(
                        'mute-effective',
                        {'item': item.mention, 'place': channel.mention}
                    ),
                    color=discord.Color.blurple()
                )
                await ctx.reply(embed=embed)

            muted_item = [
                ctx.guild.id,
                item.id,
                str(unmute_time),
                [channel.id, original_perm]
            ]
            self.muted.append(muted_item)
            self.save()

            await sleep_until(unmute_time)

            overwrite = channel.overwrites_for(item)
            overwrite.send_messages = original_perm
            await channel.set_permissions(item, overwrite=overwrite)

            self.muted.remove(muted_item)
            self.save()

        else:
            if isinstance(item, discord.Role):
                await ctx.reply(self.l10n.format_value('mute-role-not-allowed'))
                return

            mute_role_id = self.bot.c.execute(
                'select Mute_Role from guilds where ID = ?', (ctx.guild.id,)
            ).fetchone()
            if not mute_role_id:
                await ctx.reply(self.l10n.format_value('mute-role-notfound'))
                return

            await item.add_roles(ctx.guild.get_role(mute_role_id))

            muted_item = [
                ctx.guild.id,
                item.id,
                str(unmute_time),
                mute_role_id
            ]
            self.muted.append(muted_item)
            self.save()

            embed = discord.Embed(
                description=self.l10n.format_value(
                    'mute-effective',
                    {'item': item.mention, 'place': ctx.guild.name}
                ),
                color=discord.Color.blurple()
            )
            await ctx.reply(embed=embed)

            await sleep_until(unmute_time)
            await item.remove_roles(mute_role)
            self.muted.remove(muted_item)
            self.save()

    async def loadMuted(self, muted_item: list[int, int, str, Union[int, list[int, bool]]]):
        """remove mute from item after mute time"""
        unmute_time = datetime.strptime(muted_item[2], '%Y-%m-%d %H:%M:%S.%f')
        await sleep_until(unmute_time)

        if not (guild := self.bot.get_guild(muted_item[0])):
            self.muted.remove(muted_item)
            self.save()
            return
        item = guild.get_member(muted_item[1]) or guild.get_role(muted_item[1])
        if not item:
            self.muted.remove(muted_item)
            self.save()
            return

        if isinstance(muted_item[3], list):
            if not (channel := guild.get_channel(muted_item[3][0])):
                self.muted.remove(muted_item)
                self.save()
                return

            overwrite = channel.overwrites_for(item)
            overwrite.send_messages = muted_item[3][1]
            await channel.set_permissions(item, overwrite=overwrite)

            self.muted.remove(muted_item)
            self.save()

        else:
            if not (mute_role := guild.get_role(muted_item[3])):
                self.muted.remove(muted_item)
                self.save()
                return

            await item.remove_roles(mute_role)
            self.muted.remove(muted_item)
            self.save()

    async def loadAllMuted(self):
        """load all muted items to be unmuted at their respective times"""
        asyncio.gather(*[self.loadMuted(muted_item) for muted_item in self.muted])

    def save(self):
        """save the data to a json file"""
        with open('db/muted.json', 'w') as muted:
            json.dump(self.muted, muted)


def setup(bot):
    """invoked when this file is attempted to be loaded as an extension"""
    bot.add_cog(Mod(bot))
