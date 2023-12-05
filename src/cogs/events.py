import asyncio
import logging
import time
import re
from typing import Literal

import discord
from discord.ext import commands

from base.cog import HyperlinkCog


class Events(HyperlinkCog):
    """Handle events"""

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
            event_type = event["event_type"]
            if message := event["message"]:
                message = message.replace("{$user}", member.mention)
                message = message.replace("{$guild}", guild.name)

            channel_id = event["channel_id"]
            if not (channel := guild.get_channel(channel_id)):
                logging.warning(f"(table: event) -> Channel ID {channel_id} not found")
                # The only event possible without a channel ID, is a DM; for
                # which, a message is needed. If that is also absent, continue.
                if not message:
                    continue

            if event_type == "join" and channel:
                await channel.send(message)
            if event_type == "welcome" and message:
                await member.send(message)

        role_ids = await self.bot.pool.fetch(
            "SELECT role_id FROM join_role WHERE guild_id = $1", guild.id
        )
        valid_roles: list[discord.Role] = []
        broken_ids = []
        for role_id in role_ids:
            if role := guild.get_role(role_id["role"]):
                valid_roles.append(role)
            else:
                broken_ids.append(role)
        if valid_roles:
            await member.add_roles(*valid_roles)
        if broken_ids:
            await self.bot.pool.execute(
                "DELETE FROM join_role WHERE role_id = ANY($1)", broken_ids
            )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Called when a member joins a guild"""
        guild = member.guild
        self.l10n = await self.bot.get_l10n(guild.id)

        # Assign the bot role if any
        if member.bot:
            bot_role_id = await self.bot.pool.fetchval(
                "SELECT bot_role FROM guild WHERE id = $1", guild.id
            )
            if bot_role := guild.get_role(bot_role_id):
                await member.add_roles(bot_role)
            return

        # Handle all generic events
        event = await self.bot.pool.fetch(
            """
            SELECT
                event_type,
                channel_id,
                message
            FROM
                guild_event
            WHERE
                guild_id = $1
                AND event_type = ANY(ARRAY['join', 'welcome'])
            """,
            guild.id,
        )
        if event:
            await self.join_handler(event, member)

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
            defender = str(entry.target)
        else:
            defender = entry.target.id
        await self.on_remove_event(
            action,
            entry.user.mention,
            defender,
            entry.guild.id,
            entry.reason,
        )

        # WARNING: Hacky code ahead. Alter with caution
        await asyncio.sleep(1.0)
        self.bot.dispatch("member_kick_ban", entry.target.id)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        try:
            await self.bot.wait_for(
                "member_kick_ban",
                check=lambda member_id: member_id == member.id,
                timeout=4.0,
            )
        except asyncio.TimeoutError:
            await self.on_remove_event(
                "leave",
                None,
                str(member),
                member.guild.id,
            )


async def setup(bot):
    await bot.add_cog(Events(bot))
