import sqlite3, json, os, discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
class IGN(commands.Cog):
    def __init__(self):
        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

    @commands.group(name='ign')
    async def ign(self, ctx):
        # Gets details of user from the database
        self.c.execute('SELECT * FROM main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        tuple = self.c.fetchone()
        if tuple[11] == 'False':
            await ctx.send(f'Only members with a verified email can use this command, {ctx.author.mention}.')
            raise Exception('Permission Denied (Absence of a verified email)')
        if not ctx.invoked_subcommand:
            await ctx.send('Invalid IGN command passed.')

    @ign.command(name='add')
    async def add(self, ctx):
        # Assigns message content to variable
        try:
            content = ctx.message.content.split('add ')[1].split(' ')
        except:
            # Sends an embed with a list of all available games
            msg = ''
            for i in json.loads(os.getenv('Games')):
                msg += f'\n{i}'
            embed = discord.Embed(
                title = 'Here is a list of the games that you can add an IGN for:',
                description = msg,
                color = discord.Colour.blurple()
            )
            await ctx.send(embed = embed)
            return
        # Exit if IGN is missing
        try:
            ign = content[1]
        except:
            await ctx.send('Missing arguements')
            return
        # Checks if the game exists in the database
        games = json.loads(os.getenv('Games'))
        if content[0] not in games:
            await ctx.send(f'The entered game does not exist in the database, {ctx.author.mention}. If you want it added, contact a moderator.')
            return
        # Gets details of user from the database
        self.c.execute('SELECT * FROM main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        tuple = self.c.fetchone()
        igns = json.loads(tuple[14])
        # Adds IGN to the database
        igns[content[0]] = content[1]
        self.c.execute('UPDATE main set IGN = (:ign) where Discord_UID = (:uid)', {'ign': json.dumps(igns), 'uid': ctx.author.id})
        self.conn.commit()
        await ctx.send(f'IGN for {content[0]} added successfully, {ctx.author.mention}.')

    @ign.command(name='show')
    async def show(self, ctx):
        # Assigns message content to variable
        try:
            content = ctx.message.content.split('show ')[1]
        except:
            content = str(ctx.author)
            member = ctx.author
        # Checks if the game exists in the database
        try:
            game = content.split(' ')[1]
            games = json.loads(os.getenv('Games'))
            if game not in games:
                await ctx.send(f'The entered game does not exist in the database, {ctx.author.mention}. If you want it added, contact a moderator.\nFor a list of available games, type `{prefix}ign add`')
                return
            content = content.split(' ')[0]
            single = True
        except:
            single = False
        # Formats the usertag and puts it in a variable
        try:
            user = content.replace('`', '').replace('@', '')
        except:
            await ctx.send('Missing arguement: Usertag')
            return
        member = ctx.guild.get_member_named(user)
        # Gets details of user from the database
        self.c.execute('SELECT * FROM main where Discord_UID = (:uid)', {'uid': member.id})
        tuple = self.c.fetchone()
        igns = json.loads(tuple[14])
        # Exit if no IGN exists
        if not igns:
            await ctx.send(f'`{member}` did not add any IGN')
            return
        if single:
            if game in igns:
                await ctx.send(igns[game])
            else:
                await ctx.send(f'`{member}` did not add any IGN for {game}')
            return
        ign = ''
        for key in igns:
            ign += f'\n**{key}:** {igns[key]}'
        embed = discord.Embed(
            title = 'IGNs:',
            description = ign,
            color = member.top_role.color
        )
        embed.set_author(name = member, icon_url = member.avatar_url)
        embed.set_thumbnail(url = member.avatar_url)
        if ctx.author != member:
            embed.set_footer(text = f'Requested by: {ctx.author}', icon_url = ctx.author.avatar_url)
        await ctx.send(embed = embed)

    @ign.command(name='delete')
    async def delete(self, ctx):
        # Gets details of user from the database
        self.c.execute('SELECT * FROM main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        tuple = self.c.fetchone()
        igns = json.loads(tuple[14])
        # Exit if no IGN exists
        if not igns:
            await ctx.send(f'You do not any stored IGN to remove, {ctx.author.mention}.')
            return
        try:
            game = ctx.message.content.split('delete ')[1]
        except:
            # Remove all existing IGNs of the user from the database
            self.c.execute('UPDATE main SET IGN = "{}" where Discord_UID = (:uid)', {'uid': ctx.author.id})
            self.conn.commit()
            await ctx.send(f'Removed all existing IGNs successfully, {ctx.author.mention}.')
            return
        games = json.loads(os.getenv('Games'))
        # Checks if the game exists in the database
        if game not in games:
            await ctx.send(f'The entered game does not exist in the database, {ctx.author.mention}. If you want it added, contact a moderator.\nFor a list of available games, type `{prefix}ign add`')
            return
        igns = json.loads(tuple[14])
        if game in igns:
            igns.pop(game)
        else:
            await ctx.send(f'You do not any stored IGN for {game}, {ctx.author.mention}.')
            return
        # Remove requested IGN of the user from the database
        self.c.execute('UPDATE main SET IGN = (:ign) where Discord_UID = (:uid)', {'ign': json.dumps(igns), 'uid': ctx.author.id})
        self.conn.commit()
        await ctx.send(f'IGN for {game} removed successfully, {ctx.author.mention}.')
