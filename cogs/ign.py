import json
from utils.l10n import get_l10n

import discord
from discord.ext import commands

from typing import Optional

class IGN(commands.Cog):
    """Store IGNs for games"""

    def __init__(self, bot):
        self.bot = bot

        with open('db/games.json') as f:
            self.games = json.load(f)

    def getIGNs(self, author_id: int) -> dict[str, str]:
        """return the IGNs for the given user"""
        igns = self.bot.c.execute(
            'select IGN from main where Discord_UID = (:uid)',
            {'uid': author_id}
        ).fetchone()[0]
        return json.loads(igns)

    async def cog_check(self, ctx) -> bool:
        self.l10n = get_l10n(ctx.guild.id if ctx.guild else 0, 'ign')
        return self.bot.verificationCheck(ctx)

    @commands.group(invoke_without_command=True)
    async def ign(self, ctx):
        """Show the list of eligible games for which an IGN can be added.

        This is also the parent command to perform any read/write operations \
        to any of the user's IGNs.
        """
        if not self.games:
            await ctx.reply(self.l10n.format_value('game-list-notfound'))
            return

        msg = ''
        for game in self.games:
            msg += f'\n{game}'

        embed = discord.Embed(
            title = self.l10n.format_value('game-list'),
            description = msg,
            color = discord.Color.blurple()
        )
        await ctx.send(embed=embed)

    @ign.command()
    async def add(self, ctx, game: str, ign: str):
        """Add an IGN for the given game.

        Parameters
        ------------
        `game`: <class 'str'>
            The game for which an IGN is to be stored. It is case insensitive \
            and can only contain a game that is stored in the memory \
            (``games.json``); available games can be checked via the `ign` command.

        `ign`: <class 'str'>
            The IGN for the specified game. This can be anything as long as it \
            it is a string (yes, a link too). However, this cannot contain \
            tags like user/role mentions or `@everyone` and `@here`.
        """
        flag = False
        for allowed_game in self.games:
            if game.lower() == allowed_game.lower():
                flag = True
                break
        if not flag:
            await ctx.reply(self.l10n.format_value('game-notfound', {'game': game, 'prefix': ctx.prefix}))
            return

        if '@everyone' in ign or '@here' in ign:
            await ctx.reply(self.l10n.format_value('nice-try'))
            return

        igns = self.getIGNs(ctx.author.id)
        igns[allowed_game] = ign
        self.bot.c.execute(
            'update main set IGN = (:ign) where Discord_UID = (:uid)',
            {'ign': json.dumps(igns), 'uid': ctx.author.id}
        )
        self.bot.db.commit()

        await ctx.reply(self.l10n.format_value('add-success', {'game': allowed_game}))

    @ign.command()
    async def show(self, ctx, user: Optional[discord.Member], *, game: str=None):
        """Show the IGN(s) of a user.

        Displays one or all IGNs of the author of the command or of the \
        specified user. Please note that if the specified user was not found, \
        it will be added to the `game` parameter.

        Parameters
        ------------
        `user`: Optional[discord.Member]
            The name/ID/tag of a user. If specified, the IGNs returned will be \
            of the user instead of the author of the command.

        `game`: Optional[<class 'str'>]
            The name of the game for which an IGN needs to be displayed.
            Displays all the stored IGNs if not specified.
        """
        member = user or ctx.author

        oneself = ctx.author == member

        igns = self.getIGNs(member.id)
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

        if game:
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
        embed.set_thumbnail(url=member.avatar.url)
        if not oneself:
            embed.set_footer(
                text=self.l10n.format_value('request', {'author': f'{ctx.author}'}),
                icon_url=ctx.author.avatar.url
            )

        await ctx.send(embed=embed)

    @ign.command(aliases=['del'])
    async def delete(self, ctx, game: str=None):
        """Delete an IGN for the given game or all games.

        Parameters
        ------------
        `game`: Optional[<class 'str'>]
            The game for which an IGN is to be deleted. It is case insensitive \
            and can only contain a game that has a corresponding IGN for the user.
            If this is left blank, all the stored IGNs are deleted.
        """
        igns = self.getIGNs(ctx.author.id)
        if not igns:
            await ctx.reply(self.l10n.format_value('self-igns-notfound'))
            return

        if not game:
            self.bot.c.execute(
                'update main set IGN = "{}" where Discord_UID = (:uid)',
                {'uid': ctx.author.id}
            )
            self.bot.db.commit()
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

        self.bot.c.execute(
            'update main set IGN = (:ign) where Discord_UID = (:uid)',
            {'ign': json.dumps(igns), 'uid': ctx.author.id}
        )
        self.bot.db.commit()

        await ctx.reply(self.l10n.format_value('remove-success', {'game': ign}))

def setup(bot):
    """invoked when this file is attempted to be loaded as an extension"""
    bot.add_cog(IGN(bot))
