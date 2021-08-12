import json
import sqlite3

import discord
from discord.ext import commands

from typing import Optional

class IGN(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

        try:
            with open('db/games.json') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            with open('db/games.json', 'w') as f:
                json.dump([], f)
            self.data = []

    async def cog_check(self, ctx):
        return self.bot.verificationCheck(ctx)

    @commands.group(brief='Shows the list of eligible games for which an IGN can be added.')
    async def ign(self, ctx):
        if not ctx.invoked_subcommand:
            games = self.data
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

    @ign.command(brief='Used to add an IGN for a specified game.')
    async def add(self, ctx, game, ign):
        games = self.data

        flag = False
        for allowed_game in games:
            if game.lower() == allowed_game.lower():
                flag = True
                break
        if not flag:
            await ctx.reply(f'The game, `{game}`, does not exist in the database. If you want it added, contact a moderator.\nFor a list of available games, type `{ctx.prefix}ign`')
            return

        if '@everyone' in ign or '@here' in ign:
            await ctx.reply('It was worth a try.')
            return

        self.c.execute('SELECT IGN FROM main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        tuple = self.c.fetchone()
        igns = json.loads(tuple[0])

        igns[allowed_game] = ign
        self.c.execute('UPDATE main set IGN = (:ign) where Discord_UID = (:uid)', {'ign': json.dumps(igns), 'uid': ctx.author.id})
        self.conn.commit()

        await ctx.reply(f'IGN for {allowed_game} added successfully.')

    @ign.command(brief='Shows the IGN of the entered game (shows for all if none specified). If you want to see another user\'s IGN, type a part of their username (It is case sensitive) before the name of the game, which is also optional.')
    async def show(self, ctx, user: Optional[discord.Member]=None, game: str='all'):
        member = user or ctx.author

        if game.lower() == 'all':
            single = False
        else:
            single = True

        oneself = ctx.author == member

        self.c.execute('SELECT IGN FROM main where Discord_UID = (:uid)', {'uid': member.id})
        tuple = self.c.fetchone()
        igns = json.loads(tuple[0])

        if not igns:
            if oneself:
                await ctx.reply(f'Store some IGNs first using `{ctx.prefix}ign add`')
            else:
                embed = discord.Embed(
                    description = f'{member.mention} has not stored any IGN yet.',
                    color = member.top_role.color
                )
                await ctx.reply(embed=embed)
            return

        if single:
            flag = False
            for ign in igns:
                if game.lower() == ign.lower():
                    flag = True
                    break
            if flag:
                embed = discord.Embed(
                    description = igns[ign],
                    color = member.top_role.color
                )
                await ctx.reply(embed=embed)
            elif oneself:
                await ctx.reply(f'You have no IGN stored for {game} to show!')
            else:
                embed = discord.Embed(
                    description = f'{member.mention} has no IGN stored for {game} to show.',
                    color = member.top_role.color
                )
                await ctx.reply(embed=embed)
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

    @ign.command(brief='Deletes the IGN of the entered game. Deletes all IGNs if none entered', aliases=['del'])
    async def delete(self, ctx, game: str=None):
        self.c.execute('SELECT IGN FROM main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        tuple = self.c.fetchone()
        igns = json.loads(tuple[0])

        if not igns:
            await ctx.reply('You have no IGN stored to remove.')
            return

        if not game:
            self.c.execute('UPDATE main SET IGN = "{}" where Discord_UID = (:uid)', {'uid': ctx.author.id})
            self.conn.commit()
            await ctx.reply('Removed all existing IGNs successfully.')
            return

        flag = False
        for ign in igns:
            if game.lower() == ign.lower():
                flag = True
                break
        if flag:
            igns.pop(ign)
        else:
            await ctx.reply(f'You have no IGN stored for {ign} to remove.')
            return

        self.c.execute('UPDATE main SET IGN = (:ign) where Discord_UID = (:uid)', {'ign': json.dumps(igns), 'uid': ctx.author.id})
        self.conn.commit()

        await ctx.reply(f'IGN for {game} removed successfully.')

def setup(bot):
    bot.add_cog(IGN(bot))
