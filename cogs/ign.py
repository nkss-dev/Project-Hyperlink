import json
import sqlite3
from utils.l10n import get_l10n

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

    def get_ign(self, author_id):
        igns = self.c.execute(
            'select IGN from main where Discord_UID = (:uid)',
            {'uid': author_id}
        ).fetchone()[0]
        return json.loads(igns)

    async def cog_check(self, ctx):
        self.l10n = get_l10n(ctx.guild.id if ctx.guild else 0, 'ign')
        return self.bot.verificationCheck(ctx)

    @commands.group(brief='Shows the list of eligible games for which an IGN can be added.')
    async def ign(self, ctx):
        if not ctx.invoked_subcommand:
            if not self.data:
                await ctx.reply(self.l10n.format_value('game-list-notfound'))
                return

            msg = ''
            for i in self.data:
                msg += f'\n{i}'

            embed = discord.Embed(
                title = self.l10n.format_value('game-list'),
                    description = msg,
                    color = discord.Colour.blurple()
                )
            await ctx.send(embed=embed)
            return

    @ign.command(brief='Used to add an IGN for a specified game.')
    async def add(self, ctx, game, ign):
        flag = False
        for allowed_game in self.data:
            if game.lower() == allowed_game.lower():
                flag = True
                break
        if not flag:
            await ctx.reply(self.l10n.format_value('game-notfound', {'game': game, 'prefix': ctx.prefix}))
            return

        if '@everyone' in ign or '@here' in ign:
            await ctx.reply(self.l10n.format_value('nice-try'))
            return

        igns = self.get_ign(ctx.author.id)
        igns[allowed_game] = ign
        self.c.execute(
            'update main set IGN = (:ign) where Discord_UID = (:uid)',
            {'ign': json.dumps(igns), 'uid': ctx.author.id}
        )
        self.conn.commit()

        await ctx.reply(self.l10n.format_value('add-success', {'game': allowed_game}))

    @ign.command(brief='Shows the IGN of the entered game (shows for all if none specified). If you want to see another user\'s IGN, type a part of their username (It is case sensitive) before the name of the game, which is also optional.')
    async def show(self, ctx, user: Optional[discord.Member]=None, game: str='all'):
        member = user or ctx.author

        if game.lower() == 'all':
            single = False
        else:
            single = True

        oneself = ctx.author == member

        igns = self.get_ign(member.id)
        if not igns:
            if oneself:
                await ctx.reply(self.l10n.format_value('self-igns-notfound', {'prefix': ctx.prefix}))
            else:
                embed = discord.Embed(
                    description = self.l10n.format_value('other-igns-notfound', {'member': member.mention}),
                    color = member.top_role.color if ctx.guild else discord.Color.blurple()
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
                    color = member.top_role.color if ctx.guild else discord.Color.blurple()
                )
                await ctx.reply(embed=embed)
            elif oneself:
                await ctx.reply(self.l10n.format_value('self-ign-notfound', {'game': game}))
            else:
                embed = discord.Embed(
                    description = self.l10n.format_value('other-ign-notfound', {'member': member.mention, 'game': game}),
                    color = member.top_role.color if ctx.guild else discord.Color.blurple()
                )
                await ctx.reply(embed=embed)
            return

        ign = ''
        for game in igns:
            ign += f'\n**{game}:** {igns[game]}'
        embed = discord.Embed(
            title = self.l10n.format_value('igns-title', {'member': f'{member}'}),
            description = ign,
            color = member.top_role.color if ctx.guild else discord.Color.blurple()
        )
        embed.set_thumbnail(url=member.avatar_url)
        if not oneself:
            embed.set_footer(
                text=self.l10n.format_value('request', {'author': f'{ctx.author}'}),
                icon_url=ctx.author.avatar_url
            )

        await ctx.send(embed=embed)

    @ign.command(brief='Deletes the IGN of the entered game. Deletes all IGNs if none entered', aliases=['del'])
    async def delete(self, ctx, game: str=None):
        igns = self.get_ign(ctx.author.id)
        if not igns:
            await ctx.reply(self.l10n.format_value('self-igns-notfound'))
            return

        if not game:
            self.c.execute(
                'update main set IGN = "{}" where Discord_UID = (:uid)',
                {'uid': ctx.author.id}
            )
            self.conn.commit()
            await ctx.reply(self.l10n.format_value('remove-all-success'))
            return

        flag = False
        for ign in igns:
            if game.lower() == ign.lower():
                flag = True
                break
        if flag:
            igns.pop(ign)
        else:
            await ctx.reply(self.l10n.format_value('self-ign-notfound', {'ign': game}))
            return

        self.c.execute(
            'update main set IGN = (:ign) where Discord_UID = (:uid)',
            {'ign': json.dumps(igns), 'uid': ctx.author.id}
        )
        self.conn.commit()

        await ctx.reply(self.l10n.format_value('remove-success', {'game': ign}))

def setup(bot):
    bot.add_cog(IGN(bot))
