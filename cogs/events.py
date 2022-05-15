import json
import time
import re
from datetime import timedelta

import discord
from discord.ext import commands

from utils.l10n import get_l10n
from utils.utils import assign_student_roles, get_group_roles


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

        l10n = await get_l10n(
            message.guild.id if message.guild else 0,
            'events',
            self.bot.conn
        )

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

    async def join_handler(self, on_join, welcome, member, guild):
        # Sends welcome message on the server's channel
        if channel := guild.get_channel(on_join[0]):
            await channel.send(on_join[1].replace('{$user}', member.mention))

        # Sends welcome message to the user's DM
        if welcome:
            await member.send(welcome.replace('{$server}', guild.name))

        role_ids = await self.bot.conn.fetch(
            'SELECT role FROM join_role WHERE id = $1', guild.id
        )
        for role_id in role_ids:
            if role := guild.get_role(role_id['role']):
                await member.add_roles(role)
            else:
                await self.bot.conn.execute(
                    'DELETE FROM join_role WHERE role = $1', role_id
                )

    async def join_club_or_society(self, member) -> bool:
        batch = await self.bot.conn.fetchval(
            'SELECT batch FROM student WHERE discord_uid = $1',
            member.id
        )

        roles = await get_group_roles(self.bot.conn, batch, member.guild)
        # Exit if server isn't of a club/society
        if roles is None:
            return False

        is_member = await self.bot.conn.fetchval(
            '''
            SELECT
                EXISTS (
                    SELECT
                        *
                    FROM
                        group_discord_user
                    WHERE
                        id = $1
                        AND discord_uid = $2
                )
            ''', member.guild.id, member.id
        )

        # Assign year role if the user is a member, else assign guest role
        role_id = roles[0] if is_member else roles[1]
        if role := member.guild.get_role(role_id):
            await member.add_roles(role)
        return True

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Called when a member joins a guild"""
        guild = member.guild

        # Assign the bot role if any
        if member.bot:
            bot_role_id = await self.bot.conn.fetchval(
                'SELECT bot_role FROM guild WHERE id = $1', guild.id
            )
            if bot_role := guild.get_role(bot_role_id):
                await member.add_roles(bot_role)
            return

        # Handle all generic events
        guild_details = await self.bot.conn.fetchrow(
            '''
            SELECT
                join_channel,
                join_message,
                welcome_message
            FROM
                event
            WHERE
                guild_id = $1
            ''',
            guild.id
        )
        if guild_details:
            *on_join, welcome = guild_details
            await self.join_handler(on_join, welcome, member, guild)

        # Handle special events for club and society servers
        if await self.join_club_or_society(member):
            return

        # Handle special events for servers with verification
        server = await self.bot.conn.fetchrow(
            'SELECT * FROM verified_server WHERE id = $1', guild.id
        )
        if not server:
            return

        student = await self.bot.conn.fetchrow(
            '''
            SELECT
                section,
                sub_section,
                batch,
                hostel_number,
                verified
            FROM
                student
            WHERE
                discord_uid = $1
            ''', member.id
        )

        if student:
            if student['verified'] and server['batch'] in (0, student['batch']):
                await assign_student_roles(
                    member,
                    (
                        student['section'][:2],
                        student['sub_section'],
                        student['batch'],
                        student['hostel_number'],
                    ),
                    self.bot.conn
                )
                return
        else:
            # Sends a dm to the new user explaining that they have to verify
            instruct = self.bot.get_channel(server['instruction_channel'])
            command = self.bot.get_channel(server['command_channel'])

            l10n = await get_l10n(guild.id, 'events', self.bot.conn)
            mentions = {
                'instruction-channel': instruct.mention,
                'command-channel': command.mention,
                'owner': guild.owner.mention if guild.owner else None
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
        role = guild.get_role(server['guest_role'])
        if role:
            await member.add_roles(role)
        else:
            # Placeholder for error logging system
            pass

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
        l10n = await get_l10n(guild.id, 'events', self.bot.conn)

        events = await self.bot.conn.fetchrow(
            '''
            SELECT
                leave_channel,
                leave_message,
                kick_channel,
                kick_message,
                ban_channel,
                ban_message
            FROM
                event
            WHERE guild_id = $1
            ''', guild.id
        )
        if events:
            events = {
                'leave': (events['leave_channel'], events['leave_message']),
                'kick': (events['kick_channel'], events['kick_message']),
                'ban': (events['ban_channel'], events['ban_message']),
            }
            channel = await self.leave_handler(events, guild, member, l10n)

        verified = await self.bot.conn.fetch(
            'SELECT verified FROM student WHERE discord_uid = $1', member.id
        )
        if not verified:
            if events:
                await self.send_leave_message(channel, member, events['leave'][1])
            return

        if not verified[0]['verified']:
            await self.bot.conn.execute(
                'UPDATE student SET discord_uid = NULL WHERE discord_uid = $1',
                member.id
            )

        if events:
            await self.send_leave_message(channel, member, events['leave'][1])

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Called when any error is thrown"""
        l10n = await get_l10n(
            ctx.guild.id if ctx.guild else 0,
            'events',
            self.bot.conn
        )

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


async def setup(bot):
    await bot.add_cog(Events(bot))
