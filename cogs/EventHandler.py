import json
import sqlite3

from datetime import datetime
from re import fullmatch

import discord
from discord.ext import commands
from discord.utils import get

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open('db/emojis.json') as f:
            self.emojis = json.load(f)['utility']

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

        self.custom_errors = {
            'AccountNotLinked': 'You need to complete basic verification to use this command.',
            'AccountAlreadyLinked': 'You have already completed the basic level of verification.',
            'UserNotVerified': 'Only members with a verified email can use this command.',
            'UserAlreadyVerified': 'You are already verified.',
            'MissingModeratorRoles': 'This command needs for a moderator role to be set for this guild.',
        }

    @commands.Cog.listener()
    async def on_message(self, message):
        if fullmatch(f'<@!?{self.bot.user.id}>', message.content):
            embed = discord.Embed(
                title = 'Bot Details',
                color = discord.Color.blurple()
            )

            with open('db/guilds.json') as f:
                prefixes = json.load(f)[str(message.guild.id)]['prefix']

            embed.add_field(
                name = 'Prefixes',
                value = '\n'.join([f'{prefix[0] + 1}. {prefix[1]}' for prefix in enumerate(prefixes)]),
                inline = False
            )

            delta_uptime = datetime.utcnow() - self.bot.launch_time
            hours, remainder = divmod(int(delta_uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            days, hours = divmod(hours, 24)
            embed.add_field(name='Uptime', value=f'{days}d, {hours}h, {minutes}m, {seconds}s', inline=False)

            ping_msg = await message.channel.send('Initiated!')
            start = datetime.utcnow()
            await ping_msg.edit(content='Calculating ping...')
            delta_uptime = (datetime.utcnow() - start)
            embed.add_field(name='Response Latency', value=f'```{int(delta_uptime.total_seconds()*1000)}ms```')

            embed.add_field(name='Websocket Latency', value=f'```{int(self.bot.latency*1000)}ms```')

            await ping_msg.edit(content=None, embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild

        with open('db/guilds.json') as f:
            self.data = json.load(f)
        details = self.data[str(guild.id)]

        if member.bot:
            if bot_role := guild.get_role((details['bot_role'])):
                await member.add_roles(bot_role)
            return

        if details.get('on_join/leave'):
            if channel := self.bot.get_channel(details['on_join/leave']['join_msg'][0]):
                await channel.send(details['on_join/leave']['join_msg'][1].replace('{user}', member.mention))
            if dm := details['on_join/leave']['private_dm']:
                await member.send(dm.replace('{server}', guild.name))
            for role in details['on_join/leave']['new_roles']:
                if new_role := guild.get_role(role):
                    await member.add_roles(new_role)
                else:
                    details['on_join/leave']['new_roles'].remove(role)
                    self.save()

        if not details.get('verification'):
            return

        self.c.execute('SELECT Section, SubSection, Guilds, Verified from main where Discord_UID = (:uid)', {'uid': member.id})
        tuple = self.c.fetchone()

        if tuple:
            if tuple[3] == 'True':
                # Fetches the mutual guilds list from the user
                guilds = json.loads(tuple[2])
                # Adds the new guild id if it is a new one
                if guild.id not in guilds:
                    guilds.append(guild.id)
                guilds = json.dumps(guilds)
                # Assigning one SubSection and one Section role to the user
                role = get(guild.roles, name = tuple[0])
                await member.add_roles(role)
                role = get(guild.roles, name = tuple[1])
                await member.add_roles(role)
                # Updating the record in the database
                self.c.execute('UPDATE main SET Guilds = (:guilds) where Discord_UID = (:uid)', {'uid': member.id, 'guilds': guilds})
                self.conn.commit()
                return
        else:
            # Sends a dm to the new user explaining that they have to verify
            welcome_channel = self.bot.get_channel(details['verification']['welcome_channel'])
            commands_channel = self.bot.get_channel(details['verification']['commands_channel'])
            dm_message = f'Before you can see/use all the channels that it has, you will need to do a quick verification, the process of which is explained in {welcome_channel.mention}. Send the verification command in {commands_channel.mention}. If you have any issues with the command, contact a moderator on the server (or {guild.owner.mention}). Do try to verify even if you didn\'t understand it fully, the moderators will help you out if need be.'
            embed = discord.Embed(
                title = f'Welcome to {guild}!',
                description = dm_message,
                color = discord.Color.blurple()
            )
            embed.set_footer(text='Have fun!')
            await member.send(embed=embed)
        # Adding a role that restricts the user to view any channel but one on the server
        role = guild.get_role(details['verification']['not-verified_role'])
        await member.add_roles(role)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        details = self.data[str(member.guild.id)]
        if not details.get('on_join/leave'):
            return

        action = 'leave_msg'
        if member.guild.me.guild_permissions.view_audit_log:
            async for entry in member.guild.audit_logs(limit=5):
                if str(entry.target) == str(member):
                    if entry.action is discord.AuditLogAction.kick:
                        action = 'kick_msg'
                        break
                    elif entry.action is discord.AuditLogAction.ban:
                        action = 'ban_msg'
                        break

        channel = self.bot.get_channel(details['on_join/leave'][action][0])
        if action != 'leave_msg' and (channel := self.bot.get_channel(details['on_join/leave'][action][0])):
            message = details['on_join/leave'][action][1].replace('{user}', member.mention)
            message += '\n**Reason:** ' + (entry.reason or 'None')

            embed = discord.Embed(
                description = message,
                color = discord.Color.blurple()
            )
            await channel.send(embed=embed)
            channel = None

        if not details.get('verification'):
            return

        self.c.execute('SELECT Guilds, Verified FROM main where Discord_UID = (:uid)', {'uid': member.id})
        tuple = self.c.fetchone()
        # Exit if the user was not found
        if not tuple and channel:
            triggered = self.emojis['triggered']
            await channel.send(f'{member.mention} has left the server because they didn\'t know how to verify {triggered}')
            return
        # Fetches the mutual guilds list and removes one
        guilds = json.loads(tuple[0])
        guilds.remove(member.guild.id)
        # Remvoes their ID from the database if they don't have a verified email
        # and this was the only guild they shared with the bot
        if tuple[1] == 'False' and not guilds:
            self.c.execute('UPDATE main SET Discord_UID = NULL, Guilds = "[]" where Discord_UID = (:uid)', {'uid': member.id})
            self.conn.commit()
        # Only removes the guild ID otherwise
        else:
            self.c.execute('UPDATE main SET Guilds = (:guilds) where Discord_UID = (:uid)', {'uid': member.id, 'guilds': json.dumps(guilds)})
            self.conn.commit()
        if channel:
            message = details['on_join/leave'][action][1].replace('{user}', member.mention)
            message += '\n**Reason:** ' + (entry.reason or 'None')
            embed = discord.Embed(
                description = message,
                color = discord.Color.blurple()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        self.data[str(guild.id)] = self.bot.default_guild_details
        self.save()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        del self.data[str(guild.id)]
        self.save()

    def save(self):
        with open('db/guilds.json', 'w') as f:
            json.dump(self.data, f)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            pass

        elif isinstance(error, commands.UserInputError):
            if isinstance(error, commands.MissingRequiredArgument):
                await ctx.reply(f"'{error.param}' is a required argument that is missing.")

            elif isinstance(error, commands.BadArgument):
                if isinstance(error, commands.MessageNotFound):
                    await ctx.reply(error)

                else:
                    await ctx.reply(error)

        elif isinstance(error, commands.CheckFailure):
            if isinstance(error, commands.NotOwner):
                await ctx.reply('This command is for the bot owner only.')

            elif isinstance(error, commands.MissingPermissions):
                await ctx.reply(error)

            elif isinstance(error, commands.BotMissingPermissions):
                await ctx.reply(error)

            elif isinstance(error, commands.MissingAnyRole):
                error.missing_roles = ', '.join([ctx.guild.get_role(role).mention for role in error.missing_roles])
                embed = discord.Embed(
                    description = f'You are missing at least one of the required roles: {error.missing_roles}',
                    color = discord.Color.blurple()
                )
                await ctx.reply(embed=embed)

            elif str(error) in self.custom_errors:
                await ctx.reply(self.custom_errors[str(error)])

        elif isinstance(error, commands.CommandInvokeError):
            if isinstance(error.original, discord.errors.Forbidden):
                await ctx.reply('I am missing some permissions to execute this command. Please contact a mod to resolve this issue.')

            elif isinstance(error.original, commands.ExtensionError):
                await ctx.reply(error.original)
                await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)

        raise error

def setup(bot):
    bot.add_cog(Events(bot))
