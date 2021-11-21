import json
import time
import re
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from utils.l10n import get_l10n
from utils.utils import assign_student_roles


class Events(commands.Cog):
    """Handle events"""

    def __init__(self, bot):
        self.bot = bot
        with open('db/emojis.json') as f:
            self.emojis = json.load(f)['utility']

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Called when a message is sent"""
        if not re.fullmatch(f'<@!?{self.bot.user.id}>', message.content):
            return

        l10n = get_l10n(message.guild.id if message.guild else 0, 'events')

        embed = discord.Embed(
            title=l10n.format_value('details-title'),
            color=discord.Color.blurple()
        )

        prefixes = await self.bot.get_prefix(message)
        p_list = [f'{i+1}. {prefix}' for i, prefix in enumerate(prefixes)]
        embed.add_field(
            name=l10n.format_value('prefix'),
            value='\n'.join(p_list),
            inline=False
        )

        delta_uptime = discord.utils.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        embed.add_field(
            name=l10n.format_value('uptime'),
            value=f'{days}d, {hours}h, {minutes}m, {seconds}s',
            inline=False
        )

        ping = await message.channel.send(l10n.format_value('ping-initiate'))
        start = time.perf_counter()
        await ping.edit(content=l10n.format_value('ping-calc'))
        response_latency = (time.perf_counter() - start)

        embed.add_field(
            name=l10n.format_value('ping-r-latency'),
            value=f'```{int(response_latency*1000)}ms```'
        )
        embed.add_field(
            name=l10n.format_value('ping-w-latency'),
            value=f'```{int(self.bot.latency*1000)}ms```'
        )

        await ping.edit(content=None, embed=embed)

    async def join_handler(self, events, member, guild):
        if events:
            # Sends welcome message on the server's channel
            if channel := guild.get_channel(events[0]):
                await channel.send(events[1].replace('{$user}', member.mention))

            # Sends welcome message to the user's DM
            if events[2]:
                await member.send(events[2].replace('{$server}', guild.name))

        role_ids = self.bot.c.execute(
            'select role from join_roles where ID = ?', (guild.id,)
        ).fetchall()
        for role_id in role_ids:
            if role := guild.get_role(role_id):
                await member.add_roles(role)
            else:
                self.c.execute(
                    'delete from join_roles where role = ?', (role_id,)
                )
        self.bot.db.commit()

    async def join_club_or_society(self, member):
        server_exists = self.bot.c.execute(
            'select * from groups where Discord_Server = ?', (member.guild.id,)
        ).fetchone()
        if server_exists:
            details = self.bot.c.execute(
                '''select * from group_discord_users
                where Discord_Server = ? and Discord_UID = ?''',
                (member.guild.id, member.id,)
            ).fetchone()
            if not details:
                role = member.guild.get_role(server_exists[-1])
            else:
                passing_date = datetime(year=details[0], month=6, day=1)
                time = passing_date - datetime.utcnow()
                remaining_years = int(time.days/365)
                role = member.guild.get_role(details[-(remaining_years + 2)])
            if role:
                await member.add_roles(role)
            return True
        return False

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Called when a member joins a guild"""
        guild = member.guild

        # Assign the bot role if any
        if member.bot:
            bot_role_id = self.bot.c.execute(
                'select Bot_Role from guilds where ID = ?', (guild.id,)
            ).fetchone()
            if bot_role_id and (bot_role := guild.get_role(bot_role_id[0])):
                await member.add_roles(bot_role)
            return

        # Handle all generic events
        events = self.bot.c.execute(
            '''select Join_Channel, Join_Message, Welcome_Message
                from events where Guild_ID = ?''',
            (guild.id,)
        ).fetchone()
        await self.join_handler(events, member, guild)

        # Handle special events for club and society servers
        if await self.join_club_or_society(member):
            return

        # Handle special events for servers with verification
        details = self.bot.c.execute(
            'select * from verified_servers where ID = ?', (guild.id,)
        ).fetchone()
        if not details:
            return

        record = self.bot.c.execute(
            '''select Section, SubSection, Batch, Hostel_Number, Verified
                from main where Discord_UID = ?
            ''', (member.id,)
        ).fetchone()

        if record:
            if record[4] and (not details[1] or record[2] == details[1]):
                await assign_student_roles(member, record[:-1], self.bot.c)
                return
        else:
            # Sends a dm to the new user explaining that they have to verify
            instruction_channel = self.bot.get_channel(details[2])
            command_channel = self.bot.get_channel(details[3])

            l10n = get_l10n(guild.id, 'events')
            mentions = {
                'instruction-channel': instruction_channel.mention,
                'command-channel': command_channel.mention,
                'owner': guild.owner.mention
            }
            embed = discord.Embed(
                title=l10n.format_value('dm-title', {'guild': guild.name}),
                description=l10n.format_value('dm-description', mentions),
                color=discord.Color.blurple()
            )
            embed.set_footer(text=l10n.format_value('dm-footer'))

            try:
                await member.send(embed=embed)
            except discord.Forbidden:
                pass

        # Add a restricting guest role to the user
        role = guild.get_role(details[4])
        await member.add_roles(role)

    @staticmethod
    async def leave_handler(events, guild, member, l10n):
        time = discord.utils.utcnow()
        action = 'leave'

        if guild.me.guild_permissions.view_audit_log:
            # Checking the audit log entries to check for a kick or a ban
            async for entry in guild.audit_logs():
                check = str(entry.target) == str(member)
                if check and (time - entry.created_at) < timedelta(seconds=1):
                    if entry.action is discord.AuditLogAction.kick:
                        action = 'kick'
                        break
                    if entry.action is discord.AuditLogAction.ban:
                        action = 'ban'
                        break

        channel = guild.get_channel(events[action][0])
        if action != 'leave' and channel:
            mentions = {
                '{$user}': member.mention, '{$member}': entry.user.mention
            }
            message = re.sub(
                r'({\$\w+})', lambda x: mentions[x.group(0)],
                events[action][1]
            )

            message += l10n.format_value(
                'leave-reason', {'reason': entry.reason or 'None'})

            embed = discord.Embed(
                description=message,
                color=discord.Color.blurple()
            )
            await channel.send(embed=embed)
            channel = None

        return channel

    @staticmethod
    async def send_leave_message(channel, member, message):
        if channel:
            message = message.replace('{$user}', member.mention)
            embed = discord.Embed(
                description=message,
                color=discord.Color.blurple()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Called when a member leaves a guild"""
        guild = member.guild
        l10n = get_l10n(guild.id, 'events')

        events = self.bot.c.execute(
            '''select Leave_Channel, Leave_Message, Kick_Channel, Kick_Message,
                Ban_Channel, Ban_Message from events where Guild_ID = ?''',
            (guild.id,)
        ).fetchone()
        if events:
            events = {
                'leave': (events[0], events[1]),
                'kick': (events[2], events[3]),
                'ban': (events[4], events[5]),
            }
            channel = await self.leave_handler(events, guild, member, l10n)

        verified = self.bot.c.execute(
            'select Verified from main where Discord_UID = ?', (member.id,)
        ).fetchone()
        if not verified:
            if events:
                await self.send_leave_message(channel, member, events['leave'][1])
            return

        if not verified[0]:
            self.bot.c.execute(
                'update main set Discord_UID = null where Discord_UID = ?',
                (member.id,)
            )
            self.bot.db.commit()

        if events:
            await self.send_leave_message(channel, member, events['leave'][1])

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Called when any error is thrown"""
        l10n = get_l10n(ctx.guild.id if ctx.guild else 0, 'events')

        if isinstance(error, commands.UserInputError):
            if isinstance(error, commands.MissingRequiredArgument):
                await ctx.reply(l10n.format_value(
                        'UserInputError-MissingRequiredArgument',
                        {'arg': error.param.name}))

            elif isinstance(error, commands.BadArgument):
                if isinstance(error, commands.MessageNotFound):
                    await ctx.reply(error)

                else:
                    await ctx.reply(error)

            elif isinstance(error, commands.BadUnionArgument):
                await ctx.reply(error)

            else:
                raise error

        elif isinstance(error, commands.CommandNotFound):
            pass

        elif isinstance(error, commands.CheckFailure):
            if isinstance(error, commands.NotOwner):
                await ctx.reply(l10n.format_value('CheckFailure-NotOwner'))

            elif isinstance(error, commands.MissingPermissions):
                await ctx.reply(error)

            elif isinstance(error, commands.BotMissingPermissions):
                await ctx.reply(error)

            elif isinstance(error, commands.MissingAnyRole):
                missing_roles = []
                for role in error.missing_roles:
                    missing_roles.append(ctx.guild.get_role(role).mention)
                embed = discord.Embed(
                    description=l10n.format_value(
                        'CheckFailure-MissingAnyRole',
                        {'roles': ', '.join(missing_roles)}
                    ),
                    color=discord.Color.blurple()
                )
                await ctx.reply(embed=embed)

            else:
                prefix = ctx.clean_prefix
                help_str = prefix + self.bot.help_command.command_attrs['name']
                variables = {
                    'cmd': help_str,
                    'member': f'`{ctx.author}`'
                }
                await ctx.reply(l10n.format_value(str(error), variables))

        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, discord.errors.Forbidden):
                await ctx.reply(l10n.format_value('CommandInvokeError-Forbidden'))

            elif isinstance(error.original, commands.ExtensionError):
                await ctx.reply(error.original)
                await ctx.message.remove_reaction(
                    self.emojis['loading'], self.bot.user)

            else:
                raise error

        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(error)

        else:
            raise error


def setup(bot):
    """Called when this file is attempted to be loaded as an extension"""
    bot.add_cog(Events(bot))
