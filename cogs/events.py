import logging
import time
import re
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

from main import ProjectHyperlink
from utils.utils import get_group_roles


class Events(commands.Cog):
    """Handle events"""

    def __init__(self, bot: ProjectHyperlink):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Called when a message is sent"""
        if not re.fullmatch(f'<@!?{self.bot.user.id}>', message.content):
            return

        l10n = await self.bot.get_l10n(message.guild.id if message.guild else 0)

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

    async def join_handler(self, events, member: discord.Member):
        # Send a welcome message to a guild channel and/or the member
        guild = member.guild
        for event in events:
            types = event['event_types']
            if message := event['message']:
                message = message.replace('{$user}', member.mention)
                message = message.replace('{$guild}', guild.name)
            else:
                message = self.l10n.format_value(
                    'welcome-message',
                    {'user': member.mention}
                )

            channel_id = event['channel_id']
            if not (channel := guild.get_channel(channel_id)):
                logging.warning(f"(table: event) -> Channel ID {channel_id} not found")
                # The only event possible without a channel ID, is a DM; for
                # which, a message is needed. If that is also absent, continue.
                if not message:
                    continue

            if 'join' in types and channel:
                await channel.send(message)
            if 'welcome' in types and message:
                await member.send(message)

        role_ids = await self.bot.pool.fetch(
            'SELECT role_id FROM join_role WHERE guild_id = $1', guild.id
        )
        valid_roles: list[discord.Role] = []
        broken_ids = []
        for role_id in role_ids:
            if role := guild.get_role(role_id['role']):
                valid_roles.append(role)
            else:
                broken_ids.append(role)
        if valid_roles:
            await member.add_roles(*valid_roles)
        if broken_ids:
            await self.bot.pool.execute(
                'DELETE FROM join_role WHERE role_id = ANY($1)', broken_ids
            )

    async def join_club_or_society(self, member) -> bool:
        batch = await self.bot.pool.fetchval(
            'SELECT batch FROM student WHERE discord_id = $1',
            member.id
        )

        roles = await get_group_roles(self.bot.pool, batch, member.guild)
        # Exit if server isn't of a club/society
        if roles is None:
            return False

        is_member = await self.bot.pool.fetchval(
            '''
            SELECT
                EXISTS (
                    SELECT
                        *
                    FROM
                        club_discord_user
                    WHERE
                        guild_id = $1
                        AND discord_id = $2
                )
            ''', member.guild.id, member.id
        )

        # Assign year role if the user is a member, else assign guest role
        role_id = roles[0] if is_member else roles[1]
        if role := member.guild.get_role(role_id):
            await member.add_roles(role)
        return True

    async def assign_user_roles(self, member: discord.Member) -> bool:
        fields = await self.bot.pool.fetch(
            '''
            SELECT
                field,
                value,
                role_ids
            FROM
                guild_role
            WHERE
                guild_id = $1
            ''', member.guild.id
        )
        if not fields:
            return False

        details = await self.bot.pool.fetchrow(
            '''
            SELECT
                roll_number,
                section,
                batch,
                hostel_id,
                is_verified
            FROM
                student
            WHERE
                discord_id = $1
            ''', member.id
        )
        if not details:
            if role_id := fields['field'].get('!exists'):
                role = member.guild.get_role(role_id)
                if role:
                    await member.add_roles(role)
                else:
                    # Placeholder for error logging system
                    pass
            return True

        roles: list[discord.Role] = []
        for field in fields:
            if value := details.get(field['field']):
                if str(value) != field['value']:
                    continue
                for role_id in field['role_ids']:
                    if role := member.guild.get_role(role_id):
                        roles.append(role)
                    else:
                        # Placeholder for error logging system
                        pass

        await member.add_roles(*roles)
        return True

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Called when a member joins a guild"""
        guild = member.guild
        self.l10n = await self.bot.get_l10n(guild.id)

        # Assign the bot role if any
        if member.bot:
            bot_role_id = await self.bot.pool.fetchval(
                'SELECT bot_role FROM guild WHERE id = $1', guild.id
            )
            if bot_role := guild.get_role(bot_role_id):
                await member.add_roles(bot_role)
            return

        # Handle all generic events
        event = await self.bot.pool.fetch(
            '''
            SELECT
                event_types,
                channel_id,
                message
            FROM
                event
            WHERE
                guild_id = $1
                AND (
                    'join' = ANY(event_types)
                    OR 'weclome' = ANY(event_types)
                )
            ''', guild.id
        )
        if event:
            await self.join_handler(event, member)

        # Handle special events for club and society servers
        if await self.join_club_or_society(member):
            return

        # Handle special events for NITKKR servers
        # which assign roles based on student details
        if await self.assign_user_roles(member):
            return

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
        l10n = await self.bot.get_l10n(guild.id)

        events = await self.bot.pool.fetchrow(
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

        verified = await self.bot.pool.fetch(
            'SELECT verified FROM student WHERE discord_uid = $1', member.id
        )
        if not verified:
            if events:
                await self.send_leave_message(channel, member, events['leave'][1])
            return

        if not verified[0]['verified']:
            await self.bot.pool.execute(
                'UPDATE student SET discord_uid = NULL WHERE discord_uid = $1',
                member.id
            )

        if events:
            await self.send_leave_message(channel, member, events['leave'][1])


async def setup(bot):
    await bot.add_cog(Events(bot))
