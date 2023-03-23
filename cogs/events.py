import logging
import time
import re
from typing import Literal

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
        if not re.fullmatch(f"<@!?{self.bot.user.id}>", message.content):
            return

        l10n = await self.bot.get_l10n(message.guild.id if message.guild else 0)

        embed = discord.Embed(
            title=l10n.format_value("details-title"),
            color=discord.Color.blurple(),
        )

        prefixes = await self.bot.get_prefix(message)
        p_list = [f"{i+1}. {prefix}" for i, prefix in enumerate(prefixes)]
        embed.add_field(
            name=l10n.format_value("prefix"),
            value="\n".join(p_list),
            inline=False,
        )

        embed.add_field(
            name=l10n.format_value("uptime"),
            value=discord.utils.format_dt(self.bot.launch_time, "R"),
            inline=False,
        )

        ping = await message.channel.send(l10n.format_value("ping-initiate"))
        start = time.perf_counter()
        await ping.edit(content=l10n.format_value("ping-calc"))
        response_latency = time.perf_counter() - start

        embed.add_field(
            name=l10n.format_value("ping-r-latency"),
            value=f"```{int(response_latency*1000)}ms```",
        )
        embed.add_field(
            name=l10n.format_value("ping-w-latency"),
            value=f"```{int(self.bot.latency*1000)}ms```",
        )

        await message.channel.send(embed=embed)
        await ping.delete()

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

    async def on_remove_event(
        self,
        action: Literal["ban", "kick", "leave"],
        attacker: str | None,
        defender: int | str,
        guild_id: int,
        reason: str | None = None,
    ):
        response = await self.bot.pool.fetchrow(
            """
            SELECT
                channel_id,
                message
            FROM
                guild_event
            WHERE
                guild_id = $1
                AND event_type = $2
            """,
            guild_id,
            action,
        )
        if response is not None:
            channel_id, message = response
        else:
            return

        channel = self.bot.get_channel(channel_id)
        if channel is not None:
            assert isinstance(channel, discord.TextChannel)
        else:
            self.bot.logger.warning(
                f"Channel id `{channel_id}` not found for guild `{guild_id}` in table `guild_event`"
            )
            return

        mentions = {
            "attacker": attacker,
            "defender": defender,
        }
        l10n = await self.bot.get_l10n(guild_id)
        if message is None:
            # TODO: Add a set of Among Us style leave messages chosen from randomly
            message = l10n.format_value(f"{action.title()}Event", mentions)
        else:
            message = re.sub(r"({\$\w+})", lambda x: mentions[x.group(0)], message)

        colours = {
            "ban": discord.Color.red(),
            "kick": discord.Color.orange(),
            "leave": discord.Color.blurple(),
        }
        embed = discord.Embed(
            color=colours[action],
            description=message,
            timestamp=discord.utils.utcnow(),
        )
        if reason is not None:
            embed.set_footer(
                text=l10n.format_value("RemoveReason", {"reason": reason}),
            )
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        """Handle kick and ban entries"""
        if entry.action is discord.AuditLogAction.kick:
            action = "kick"
        elif entry.action is discord.AuditLogAction.ban:
            action = "ban"
        else:
            return

        assert isinstance(entry.user, discord.Member | discord.User)
        assert isinstance(entry.target, discord.User | discord.Object)

        if isinstance(entry.target, discord.User):
            defender = entry.target.mention
        else:
            defender = entry.target.id
        await self.on_remove_event(
            action,
            entry.user.mention,
            defender,
            entry.guild.id,
            entry.reason,
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        # TODO: Add conditional to check if it was self-leave or not
        await self.on_remove_event("leave", None, member.mention, member.guild.id)


async def setup(bot):
    await bot.add_cog(Events(bot))
