import json
import sqlite3
from utils.l10n import get_l10n

from datetime import datetime, timedelta
from re import fullmatch

import discord
from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.launch_time = datetime.utcnow()

        with open('db/emojis.json') as f:
            self.emojis = json.load(f)['utility']

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

    @commands.Cog.listener()
    async def on_message(self, message):
        if not fullmatch(f'<@!?{self.bot.user.id}>', message.content):
            return

        l10n = get_l10n(message.guild.id if message.guild else 0, 'EventHandler')

        embed = discord.Embed(
            title = l10n.format_value('details-title'),
            color = discord.Color.blurple()
        )

        if message.guild:
            prefixes = self.bot.guild_data[str(message.guild.id)]['prefix']
            embed.add_field(
                name = l10n.format_value('prefix'),
                value = '\n'.join([f'{i+1}. {prefix}' for i, prefix in enumerate(prefixes)]),
                inline = False
            )
        else:
            embed.add_field(name=l10n.format_value('prefix'), value='%', inline=False)

        delta_uptime = datetime.utcnow() - self.bot.launch_time
        hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        embed.add_field(
            name = l10n.format_value('uptime'),
            value = f'{days}d, {hours}h, {minutes}m, {seconds}s',
            inline = False
        )

        ping_msg = await message.channel.send(l10n.format_value('ping-initiate'))
        start = datetime.utcnow()
        await ping_msg.edit(content=l10n.format_value('ping-calc'))
        delta_uptime = (datetime.utcnow() - start)

        embed.add_field(
            name = l10n.format_value('ping-r-latency'),
            value = f'```{int(delta_uptime.total_seconds()*1000)}ms```'
        )
        embed.add_field(
            name = l10n.format_value('ping-w-latency'),
            value = f'```{int(self.bot.latency*1000)}ms```'
        )

        await ping_msg.edit(content=None, embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
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
            for role in details['roles']['join']:
                if new_role := guild.get_role(role):
                    await member.add_roles(new_role)
                else:
                    self.bot.guild_data[str(guild.id)]['roles']['join'].remove(role)
                    self.save()

        if not details.get('verification'):
            return

        tuple = self.c.execute(
            'select Section, SubSection, Guilds, Verified from main where Discord_UID = (:uid)',
            {'uid': member.id}
        ).fetchone()

        if tuple:
            if tuple[3] == 'True':
                # Adding the guild ID to the user's details
                guilds = json.loads(tuple[2])
                if guild.id not in guilds:
                    guilds.append(guild.id)
                guilds = json.dumps(guilds)

                # Assigning Section and Sub-Section roles to the user
                role = discord.utils.get(guild.roles, name = tuple[0])
                await member.add_roles(role)
                role = discord.utils.get(guild.roles, name = tuple[1])
                await member.add_roles(role)

                self.c.execute(
                    'update main set Guilds = (:guilds) where Discord_UID = (:uid)',
                    {'uid': member.id, 'guilds': guilds}
                )
                self.conn.commit()
                return
        else:
            # Sends a dm to the new user explaining that they have to verify
            instruction = self.bot.get_channel(details['verification']['instruction'])
            command = self.bot.get_channel(details['verification']['command'])

            l10n = get_l10n(guild.id, 'EventHandler')
            keys = {
                'instruction-channel': instruction.mention,
                'command-channel': command.mention,
                'owner': guild.owner.mention
            }
            embed = discord.Embed(
                title = l10n.format_value('dm-title', {'guild': guild.name}),
                description = l10n.format_value('dm-description', keys),
                color = discord.Color.blurple()
            )
            embed.set_footer(text=l10n.format_value('dm-footer'))

            try:
                await member.send(embed=embed)
            except:
                pass

        # Adding a role that restricts the user to view any channel on the server
        role = guild.get_role(details['verification']['not-verified_role'])
        await member.add_roles(role)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        time = discord.utils.utcnow()
        guild = member.guild

        details = self.bot.guild_data[str(guild.id)]

        if not (events := details.get('events')):
            return

        l10n = get_l10n(guild.id, 'EventHandler')

        action = 'leave'
        if guild.me.guild_permissions.view_audit_log:
            # Checking the audit log entries to check for a kick or a ban
            async for entry in guild.audit_logs():
                if str(entry.target) == str(member) and (time - entry.created_at) < timedelta(seconds=1):
                    if entry.action is discord.AuditLogAction.kick:
                        action = 'kick'
                        break
                    if entry.action is discord.AuditLogAction.ban:
                        action = 'ban'
                        break

        channel = self.bot.get_channel(events[action][0])
        if action != 'leave' and channel:
            for i in (('{user}', member.mention), ('{member}', entry.user.mention)):
                events[action][1].replace(*i)
            message = events[action][1]
            message += l10n.format_value('leave-reason', {'reason': entry.reason or 'None'})

            embed = discord.Embed(
                description = message,
                color = discord.Color.blurple()
            )
            await channel.send(embed=embed)
            channel = None

        if not details.get('verification'):
            if channel:
                message = events['leave'][1].replace('{user}', member.mention)

                embed = discord.Embed(
                    description = message,
                    color = discord.Color.blurple()
                )
                await channel.send(embed=embed)
            return

        tuple = self.c.execute(
            'select Guilds, Verified FROM main where Discord_UID = (:uid)',
            {'uid': member.id}
        ).fetchone()

        if not tuple and channel:
            keys = {
                'member': member.mention,
                'emoji': self.emojis['triggered']
            }
            await channel.send(l10n.format_value('leave-verification-notfound', keys))
            return

        # Removing the guild ID from the user's details
        guilds = json.loads(tuple[0])
        guilds.remove(guild.id)

        # Removing the user's entry if they don't share any guild with the bot and are not verified
        if tuple[1] == 'False' and not guilds:
            self.c.execute(
                'update main set Discord_UID = NULL, Guilds = "[]" where Discord_UID = (:uid)',
                {'uid': member.id}
            )
            self.conn.commit()

        else:
            self.c.execute(
                'update main set Guilds = (:guilds) where Discord_UID = (:uid)',
                {'uid': member.id, 'guilds': json.dumps(guilds)}
            )
            self.conn.commit()

        # Sends exit message to the server's channel
        if channel:
            message = events['leave'][1].replace('{user}', member.mention)

            embed = discord.Embed(
                description = message,
                color = discord.Color.blurple()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.bot.guild_data[str(guild.id)] = self.bot.default_guild_details
        self.save()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        del self.bot.guild_data[str(guild.id)]
        self.save()

    def save(self):
        with open('db/guilds.json', 'w') as f:
            json.dump(self.bot.guild_data, f)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        l10n = get_l10n(ctx.guild.id if ctx.guild else 0, 'EventHandler')

        if isinstance(error, commands.CommandNotFound):
            pass

        elif isinstance(error, commands.UserInputError):
            if isinstance(error, commands.MissingRequiredArgument):
                await ctx.reply(l10n.format_value('UserInputError-MissingRequiredArgument', {'arg': error.param.name}))

            elif isinstance(error, commands.BadArgument):
                if isinstance(error, commands.MessageNotFound):
                    await ctx.reply(error)

                else:
                    await ctx.reply(error)

        elif isinstance(error, commands.CheckFailure):
            if isinstance(error, commands.NotOwner):
                await ctx.reply(l10n.format_value('CheckFailure-NotOwner'))

            elif isinstance(error, commands.MissingPermissions):
                await ctx.reply(error)

            elif isinstance(error, commands.BotMissingPermissions):
                await ctx.reply(error)

            elif isinstance(error, commands.MissingAnyRole):
                roles = ', '.join([ctx.guild.get_role(role).mention for role in error.missing_roles])
                embed = discord.Embed(
                    description = l10n.format_value('CheckFailure-MissingAnyRole', {'roles': roles}),
                    color = discord.Color.blurple()
                )
                await ctx.reply(embed=embed)

            else:
                await ctx.reply(l10n.format_value(str(error)))

        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, discord.errors.Forbidden):
                await ctx.reply(l10n.format_value('CommandInvokeError-Forbidden'))

            elif isinstance(error.original, commands.ExtensionError):
                await ctx.reply(error.original)
                await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)

        raise error

def setup(bot):
    bot.add_cog(Events(bot))
