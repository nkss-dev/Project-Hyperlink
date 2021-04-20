import sqlite3, json, os, discord
from discord.ext import commands

class IGN(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()
        try:
            with open('db/games.json') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {}

    @commands.group(name='ign')
    async def ign(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.reply('Invalid IGN command passed.')
            return
        self.c.execute('SELECT Verified FROM main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        tuple = self.c.fetchone()
        if not tuple:
            raise Exception('AccountNotLinked')
        if tuple[0] == 'False':
            raise Exception('EmailNotVerified')

    @ign.command(name='add')
    async def add(self, ctx, *args):
        # Loads the available games from the database
        games = self.data[str(ctx.guild.id)]
        if not args:
            msg = ''
            for i in games:
                msg += f'\n{i}'
            # Sends an embed with a list of all available games
            embed = discord.Embed(
                title = 'Here is a list of the games that you can add an IGN for:',
                description = msg,
                color = discord.Colour.blurple()
            )
            await ctx.send(embed=embed)
            return
        # Exit if the game does not exist in the database
        if args[0] not in games:
            await ctx.reply(f'The entered game does not exist in the database. If you want it added, contact a moderator.\nFor a list of available games, type `{prefix}ign add`')
            return
        # Exit if IGN is missing
        if len(args) < 2:
            await ctx.reply('Missing arguements')
            return
        if '@everyone' in args[1] or '@here' in args[1]:
            await ctx.reply('It was worth a try.')
            return
        # Gets details of user from the database
        self.c.execute('SELECT IGN FROM main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        tuple = self.c.fetchone()
        igns = json.loads(tuple[0])
        # Adds IGN to the database
        igns[args[0]] = args[1]
        self.c.execute('UPDATE main set IGN = (:ign) where Discord_UID = (:uid)', {'ign': json.dumps(igns), 'uid': ctx.author.id})
        self.conn.commit()
        await ctx.reply(f'IGN for {args[0]} added successfully.')

    @ign.command(name='show')
    async def show(self, ctx, *args):
        # Setting single to False will show all the IGNs for the requested user
        if not args:
            member = ctx.author
            single = False
        elif 'all' in args[0].lower():
            single = False
        else:
            single = True
        # Loads the available games from the database
        games = self.data[str(ctx.guild.id)]
        # Exit if the game does not exist in the database
        if single and args[0] not in games:
            await ctx.reply(f'The entered game does not exist in the database. If you want it added, contact a moderator.\nFor a list of available games, type `{prefix}ign add`')
            return
        oneself = True
        if len(args) == 1:
            member = ctx.author
            game = args[0]
        elif len(args) == 2:
            member = ctx.guild.get_member_named(args[1])
            if not member:
                await ctx.reply(f'Member with the name `{args[1]}` not found!')
                return
            game = args[0]
            oneself = False
        # Gets details of user from the database
        self.c.execute('SELECT IGN FROM main where Discord_UID = (:uid)', {'uid': member.id})
        tuple = self.c.fetchone()
        igns = json.loads(tuple[0])
        # Exit if no IGN exists
        if not igns:
            if oneself:
                await ctx.reply('You have no IGN stored to show!')
            else:
                await ctx.reply(f'`{member}` has no IGN stored to show.')
            return
        if single:
            if game in igns:
                await ctx.reply(embed=discord.Embed(description=igns[game],color=member.top_role.color))
            elif oneself:
                await ctx.reply(f'You have no IGN stored for {game} to show!')
            else:
                await ctx.reply(f'`{member}` has no IGN stored for {game} to show.')
            return
        ign = ''
        for game in igns:
            ign += f'\n**{game}:** {igns[game]}'
        embed = discord.Embed(
            title = f'{member}\'s IGNs:\n',
            description = ign,
            color = member.top_role.color
        )
        embed.set_thumbnail(url=member.avatar_url)
        if not oneself:
            embed.set_footer(text=f'Requested by: {ctx.author}', icon_url=ctx.author.avatar_url)
        await ctx.send(embed=embed)

    @ign.command(name='delete', aliases=['del'])
    async def delete(self, ctx, *args):
        # Gets details of user from the database
        self.c.execute('SELECT IGN FROM main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        tuple = self.c.fetchone()
        igns = json.loads(tuple[0])
        # Exit if no IGN exists
        if not igns:
            await ctx.reply('You have no IGN stored to remove.')
            return
        if not args:
            # Remove all existing IGNs of the user from the database
            self.c.execute('UPDATE main SET IGN = "{}" where Discord_UID = (:uid)', {'uid': ctx.author.id})
            self.conn.commit()
            await ctx.reply('Removed all existing IGNs successfully.')
            return
        # Loads the available games from the database
        games = self.data[str(ctx.guild.id)]
        # Checks if the game exists in the database
        if game not in games:
            await ctx.reply(f'The entered game does not exist in the database. If you want it added, contact a moderator.\nFor a list of available games, type `{prefix}ign add`')
            return
        if game in igns:
            igns.pop(game)
        else:
            await ctx.reply(f'You have no IGN stored for {game} to remove.')
            return
        # Remove requested IGN of the user from the database
        self.c.execute('UPDATE main SET IGN = (:ign) where Discord_UID = (:uid)', {'ign': json.dumps(igns), 'uid': ctx.author.id})
        self.conn.commit()
        await ctx.reply(f'IGN for {game} removed successfully.')

def setup(bot):
    bot.add_cog(IGN(bot))
