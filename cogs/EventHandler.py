import discord, json
from discord.ext import commands

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged on as {self.bot.user}!\n')
        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=f'@{self.bot.user.name}'))

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Exit if the user is a bot
        if member.bot or member.guild.id != 783215699707166760:
            return
        conn = sqlite3.connect('db/details.db')
        c = conn.cursor()
        # Checks if the user who joined is already in the database or not
        c.execute('SELECT * from main where Discord_UID = (:uid)', {'uid': member.id})
        tuple = c.fetchone()
        guild = member.guild
        if tuple:
            # Fetches the mutual guilds list from the user
            guilds = json.loads(tuple[10])
            # Adds the new guild id if it's a new one
            if guild.id not in guilds:
                guilds.append(guild.id)
            guilds = json.dumps(guilds)
            # Assigning one SubSection and one Section role to the user
            role = get(guild.roles, name = tuple[2])
            await member.add_roles(role)
            role = get(guild.roles, name = tuple[3])
            await member.add_roles(role)
            # Updating the record in the database
            c.execute('UPDATE main SET Guilds = (:guilds) where Discord_UID = (:uid)', {'uid': member.id, 'guilds': guilds})
            conn.commit()
            return
        # Adding the 'Not-Verified' role if the user details do not exist in the database
        role = get(guild.roles, name = 'Not-Verified')
        await member.add_roles(role)
        # Sends a dm to the new user explaining that they have to verify
        dm_message = '''Welcome to the NITKKR'24 server!
        Before you can see/use all the channels that it has, you'll need to do a quick verification. The process of which is explained in the #welcome channel of the server. Please do not send the command to this dm as it will not be read, instead send it on the #commands channel on the server. If you have any issues with the command, @Priyanshu will help you out personally on the channel. But do try even if you didn't understand.
        Have fun!'''
        await member.send(dm_message)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        if member.bot or member.guild.id == 336642139381301249:
            return
        conn = sqlite3.connect('db/details.db')
        c = conn.cursor()
        # Gets details of user from the database
        c.execute('SELECT * FROM main where Discord_UID = (:uid)', {'uid': member.id})
        tuple = c.fetchone()
        channel = client.get_channel(783215699707166763)
        # Exit if the user was not found
        if not tuple:
            await channel.send(f'{member.mention} has left the server because they didn\'t know how to verify <a:triggered:803206114623619092>')
            return
        # Fetches the mutual guilds list from the user
        guilds = json.loads(tuple[10])
        # Removes the guild from the list
        guilds.remove(member.guild.id)
        # Remvoes their ID from the database if they don't have a verified email
        # and this was the only guild they shared with the bot
        if tuple[11] == 'False' and guilds:
            guilds = json.dumps(guilds)
            c.execute('UPDATE main SET Discord_UID = NULL, Guilds = (:guilds) where Discord_UID = (:uid)', {'uid': member.id, 'guilds': guilds})
            conn.commit()
        # Only removes the guild ID otherwise
        else:
            guilds = json.dumps(guilds)
            c.execute('UPDATE main SET Guilds = (:guilds) where Discord_UID = (:uid)', {'uid': member.id, 'guilds': guilds})
            conn.commit()
        await channel.send(f'{member.mention} has left the server.')

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        if before.channel and before.channel != after.channel:
            try:
                with open('db/VCs.json') as f:
                    data = json.load(f)
            except FileNotFoundError:
                data = []
            if before.channel.id in data:
                if not len(before.channel.members):
                    await before.channel.delete()
                    data.remove(before.channel.id)
                with open('db/VCs.json', 'w') as f:
                    json.dump(data, f)
                return
        if not after.channel:
            return
        if after.channel.id not in [825422681695846430, 825456619211063327]:
            return
        if member.nick:
            member_name = member.nick
        else:
            member_name = member.name
        vc = await member.guild.create_voice_channel(f'{member_name}\'s Party', category=after.channel.category)
        await member.move_to(vc)
        try:
            with open('db/VCs.json') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = []
        if vc.id not in data:
            data.append(vc.id)
            with open('db/VCs.json', 'w') as f:
                json.dump(data, f)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if type(error).__name__ == 'MissingRequiredArgument':
            error_msg = error.args[0].split(' ', 1)
            await ctx.reply(f'\'{error_msg[0]}\' {error_msg[1]}')
        if type(error).__name__ == 'MissingPermissions':
            await ctx.reply(error.args[0])
        elif type(error).__name__ == 'CommandInvokeError':
            if 'Missing Permissions' in error.args[0]:
                await ctx.reply('I\'m missing some permissions to execute this command. Please contact a mod to resolve this issue.')
            if 'TypeError' in error.args[0]:
                print(error)
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

def setup(bot):
    bot.add_cog(Events(bot))
