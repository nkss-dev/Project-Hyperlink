import json
import re
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from utils.l10n import get_l10n


class Events(commands.Cog):
    """Handle events"""

    def __init__(self, bot):
        self.bot = bot
        self.bot.launch_time = datetime.utcnow()

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

        if message.guild:
            prefixes = self.bot.guild_data[str(message.guild.id)]['prefix']
            p_list = [f'{i+1}. {prefix}' for i, prefix in enumerate(prefixes)]
            embed.add_field(
                name=l10n.format_value('prefix'),
                value='\n'.join(p_list),
                inline=False
            )
        else:
            embed.add_field(
                name=l10n.format_value('prefix'), value='%', inline=False)

        delta_uptime = datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        embed.add_field(
            name=l10n.format_value('uptime'),
            value=f'{days}d, {hours}h, {minutes}m, {seconds}s',
            inline=False
        )

        ping = await message.channel.send(l10n.format_value('ping-initiate'))
        start = datetime.utcnow()
        await ping.edit(content=l10n.format_value('ping-calc'))
        delta_uptime = (datetime.utcnow() - start)

        embed.add_field(
            name=l10n.format_value('ping-r-latency'),
            value=f'```{int(delta_uptime.total_seconds()*1000)}ms```'
        )
        embed.add_field(
            name=l10n.format_value('ping-w-latency'),
            value=f'```{int(self.bot.latency*1000)}ms```'
        )

        await ping.edit(content=None, embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Called when a member joins a guild"""
        guild = member.guild

        details = self.bot.guild_data[str(guild.id)]

        if member.bot:
            if botRole := guild.get_role((details['roles']['bot'])):
                await member.add_roles(botRole)
            return

        if events := details.get('events'):
            # Sends welcome message on the server's channel
            if channel := self.bot.get_channel(events['join'][0]):
                await channel.send(events['join'][1].replace('{user}', member.mention))

            # Sends welcome message to the user's DM
            if dm := events['welcome']:
                await member.send(dm.replace('{server}', guild.name))

            # Gives roles to the new user
            for role_id in details['roles']['join']:
                if role := guild.get_role(role_id):
                    await member.add_roles(role)
                else:
                    details['roles']['join'].remove(role_id)
            self.bot.guild_data[str(guild.id)] = details
            self.save()

        if not (details := details.get('verification')):
            return

        tuple = self.bot.c.execute(
            'select Section, SubSection, Verified from main where Discord_UID = ?',
            (member.id,)
        ).fetchone()

        if tuple:
            if tuple[2] == 'True':
                # Assigning Section and Sub-Section roles to the user
                if role := discord.utils.get(guild.roles, name=tuple[0]):
                    await member.add_roles(role)
                if role := discord.utils.get(guild.roles, name=tuple[1]):
                    await member.add_roles(role)

                return
        else:
            # Sends a dm to the new user explaining that they have to verify
            instruction = self.bot.get_channel(details['instruction'])
            command = self.bot.get_channel(details['command'])

            l10n = get_l10n(guild.id, 'events')
            mentions = {
                'instruction-channel': instruction.mention,
                'command-channel': command.mention,
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

        # Adding a role that restricts the user to view channels on the server
        role = guild.get_role(details['role'])
        await member.add_roles(role)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Called when a member leaves a guild"""
        time = discord.utils.utcnow()
        guild = member.guild

        details = self.bot.guild_data[str(guild.id)]

        if not (events := details.get('events')):
            return

        l10n = get_l10n(guild.id, 'events')

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

        channel = self.bot.get_channel(events[action][0])
        if action != 'leave' and channel:
            message = events[action][1].replace('{user}', member.mention)
            message = message.replace('{member}', entry.user.mention)

            message += l10n.format_value(
                'leave-reason', {'reason': entry.reason or 'None'})

            embed = discord.Embed(
                description=message,
                color=discord.Color.blurple()
            )
            await channel.send(embed=embed)
            channel = None

        if not details.get('verification'):
            if channel:
                message = events['leave'][1].replace('{user}', member.mention)

                embed = discord.Embed(
                    description=message,
                    color=discord.Color.blurple()
                )
                await channel.send(embed=embed)
            return

        verified = self.bot.c.execute(
            'select Verified from main where Discord_UID = ?', (member.id,)
        ).fetchone()

        if not verified:
            if channel:
                keys = {
                    'member': member.mention,
                    'emoji': self.emojis['triggered']
                }
                await channel.send(l10n.format_value(
                        'leave-verification-notfound', keys))
            return

        # Removing the user's entry if they don't share
        # any guild with the bot and are not verified
        if verified[0] == 'False':
            self.bot.c.execute(
                'update main set Discord_UID = null where Discord_UID = ?',
                (member.id,)
            )
            self.bot.db.commit()

        # Sends exit message to the server's channel
        if channel:
            message = events['leave'][1].replace('{user}', member.mention)

            embed = discord.Embed(
                description=message,
                color=discord.Color.blurple()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Called when the bot joins a guild"""
        self.bot.guild_data[str(guild.id)] = self.bot.default_guild_details
        self.save()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """Called when the bot leaves a guild"""
        del self.bot.guild_data[str(guild.id)]
        self.save()

    def save(self):
        """save the data to a json file"""
        with open('db/guilds.json', 'w') as f:
            json.dump(self.bot.guild_data, f)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Called when any error is thrown"""
        l10n = get_l10n(ctx.guild.id if ctx.guild else 0, 'events')

        if isinstance(error, commands.CommandNotFound):
            pass

        elif isinstance(error, commands.UserInputError):
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
                await ctx.reply(l10n.format_value(str(error)))

        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, discord.errors.Forbidden):
                await ctx.reply(l10n.format_value('CommandInvokeError-Forbidden'))

            elif isinstance(error.original, commands.ExtensionError):
                await ctx.reply(error.original)
                await ctx.message.remove_reaction(
                    self.emojis['loading'], self.bot.user)

            else:
                raise error

        else:
            raise error


def setup(bot):
    bot.add_cog(Events(bot))
