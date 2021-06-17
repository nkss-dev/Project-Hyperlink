import discord, json, sqlite3, re
from datetime import datetime
from discord.utils import get
from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open('db/guilds.json') as f:
            self.data = json.load(f)
        with open('db/emojis.json') as f:
            self.emojis = json.load(f)['utility']

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

    @commands.Cog.listener()
    async def on_message(self, message):
        if re.fullmatch(f'<@!?{self.bot.user.id}>', message.content):
            embed = discord.Embed(
            title = 'Bot Details',
            color = discord.Color.blurple()
            )

            prefixes = self.data[str(message.guild.id)]['prefix']
            embed.add_field(name='Prefixes', value='\n'.join([f'{prefix[0] + 1}. {prefix[1]}' for prefix in enumerate(prefixes)]), inline=False)

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
        details = self.data[str(guild.id)]
        if member.bot:
            if bot_role := member.guild.get_role((details['bot_role'])):
                await member.add_roles(bot_role)
            return
        if 'on_join/leave' in details:
            if channel := self.bot.get_channel(details['on_join/leave']['join_msg'][0]):
                await channel.send(details['on_join/leave']['join_msg'][1].replace('{user}', member.mention))
            if dm := details['on_join/leave']['private_dm']:
                await member.send(dm.replace('{server}', member.guild.name))
            for role in details['on_join/leave']['new_roles']:
                if new_role := member.guild.get_role(role):
                    await member.add_roles(new_role)
                else:
                    details['on_join/leave']['new_roles'].remove(role)
                    self.save()
        if 'verification' not in details:
            return
        # Checks if the user who joined is already in the database or not
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
        if 'on_join/leave' not in details:
            return
        if member.guild.me.guild_permissions.view_audit_log:
            async for entry in member.guild.audit_logs(limit=5):
                if str(entry.target) == str(member):
                    if entry.action is discord.AuditLogAction.kick:
                        action = 'kick_msg'
                        break
                    elif entry.action is discord.AuditLogAction.ban:
                        action = 'ban_msg'
                        break
                    else:
                        action = 'leave_msg'
        else:
            action = 'leave_msg'
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
        if 'verification' not in details:
            return
        # Gets details of user from the database
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
            message = details['on_join/leave']['leave_msg'][1].replace('{user}', member.mention)
            message += '\n**Reason:** ' + (entry.reason or 'None')
            embed = discord.Embed(
                description = message,
                color = discord.Color.blurple()
            )
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        default_details = {
            'prefix': ['%'],
            'mod_roles': [],
            'verification': {},
            'bot_role': 0,
            'logging_channel': [0, 0]
        }
        self.data[guild.id] = default_details
        self.save()

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        del self.data[str(guild.id)]
        self.save()

    def save():
        with open('db/guilds.json', 'w') as f:
            json.dump(self.data, f)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        if isinstance(error, commands.MissingRequiredArgument):
            error_msg = error.args[0].split(' ', 1)
            await ctx.reply(f'\'{error_msg[0]}\' {error_msg[1]}')
        elif isinstance(error, commands.MissingPermissions):
            await ctx.reply(error.args[0])
        elif isinstance(error, commands.CommandInvokeError):
            if 'Missing Permissions' in error.args[0]:
                await ctx.reply('I am missing some permissions to execute this command. Please contact a mod to resolve this issue.')
            elif 'TypeError' in error.args[0]:
                print(error)
            elif 'AccountNotLinked' in error.args[0]:
                await ctx.reply('You need to complete basic verification to use this command.')
            elif 'EmailNotVerified' in error.args[0]:
                await ctx.reply('Only members with a verified email can use this command.')
            elif 'AccountAlreadyLinked' in error.args[0]:
                await ctx.reply('You have already completed the basic level of verification')
            elif 'UserAlreadyVerified' in error.args[0]:
                await ctx.reply('You are already verified.')
            elif 'SlowmodeNotEnabled' in error.args[0]:
                await ctx.reply('This command is usable only in a channel which has slowmode enabled.')
            elif 'ExtensionAlreadyLoaded' in error.args[0] or 'ExtensionNotLoaded' in error.args[0] or 'ExtensionNotFound' in error.args[0]:
                await ctx.reply(error.args[0].split(': ')[2])
                await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)
        elif isinstance(error, commands.MessageNotFound):
            await ctx.reply(error.args[0].replace('"', "'"))
        else:
            errors = []
            for exception in error.args:
                if 'Converting to ' in exception:
                    _, instance, _, param, _ = exception.split('"')
                    errors.append('The {} parameter must be of the type \'{}\'.'.format(param, instance))
            if len(errors) > 1:
                errors = '\n'.join([f'{exception[0] + 1}. {exception[1]}' for exception in enumerate(errors)])
                await ctx.reply('The following errors occured while parsing your command:\n\n{}'.format(errors))
            elif errors:
                await ctx.reply(errors[0])
        print(f'\n{type(error).__name__}, {error.args}\n')
        raise error

def setup(bot):
    bot.add_cog(Events(bot))
