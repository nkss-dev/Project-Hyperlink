import sqlite3
from typing import Optional

import discord
from discord.ext import commands

from utils.l10n import get_l10n


class IGN(commands.Cog):
    """Store IGNs for games"""

    def __init__(self, bot):
        self.bot = bot
        self.games = []

    def get_IGNs(self, author_id: int) -> sqlite3.Cursor:
        """Return the IGNs of the given user"""
        cursor = self.bot.c.execute(
            'select * from ign where Discord_UID = ?', (author_id,)
        )
        return cursor

    async def exists(self, ctx, game) -> Optional[str]:
        """Check if entered game exists in the database"""
        result = None
        for _game in self.games:
            if game.lower() == _game[0].lower():
                result = _game[0]
                break

        if not result:
            content = self.l10n.format_value(
                'game-notfound',
                {'game': game, 'cmd': f'{ctx.clean_prefix}{ctx.command.parent}'}
            )
            await ctx.reply(content)
        return result

    async def cog_check(self, ctx) -> bool:
        self.l10n = get_l10n(ctx.guild.id if ctx.guild else 0, 'ign')
        return self.bot.verificationCheck(ctx)

    @commands.group()
    async def ign(self, ctx):
        """Show the list of eligible games for which an IGN can be added.

        This is also the parent command to perform any read/write operations \
        to any of the user's IGNs.
        """
        self.games = self.bot.c.execute(
            'select * from ign where Discord_UID = null'
        ).description[1:]
        if not self.games:
            await ctx.reply(self.l10n.format_value('game-list-notfound'))
            return

        if ctx.invoked_subcommand:
            return

        embed = discord.Embed(
            title=self.l10n.format_value('game-list'),
            description='\n'.join([game[0] for game in self.games]),
            color=discord.Color.blurple()
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
            (``games.json``).
            Available games can be checked via the `ign` command.

        `ign`: <class 'str'>
            The IGN for the specified game. This can be anything as long as \
            it is a string (yes, a link too). However, this cannot contain \
            tags like user/role mentions or `@everyone` and `@here`.
        """
        if not (game := await self.exists(ctx, game)):
            return

        if ctx.message.mentions:
            await ctx.reply(self.l10n.format_value('mentions-not-allowed'))
            return

        exists = self.get_IGNs(ctx.author.id).fetchone()
        if not exists:
            self.bot.c.execute(
                f'insert into ign (Discord_UID, {game}) values(?,?)',
                (ctx.author.id, ign,)
            )
        else:
            self.bot.c.execute(
                f'update ign set {game} = ? where Discord_UID = ?',
                (ign, ctx.author.id,)
            )
        self.bot.db.commit()

        await ctx.reply(self.l10n.format_value('add-success', {'game': game}))

    @ign.command()
    async def show(self, ctx, user: Optional[discord.Member], *, game: str = None):
        """Show the IGN(s) of a user.

        Displays one or all IGNs of the author of the command or of the \
        specified user. Please note that if the specified user was not found, \
        it will be added to the `game` parameter.

        Parameters
        ------------
        `user`: Optional[discord.Member]
            The name/ID/tag of a user. If specified, the IGNs returned will \
            be of the user instead of the author of the command.

        `game`: Optional[<class 'str'>]
            The name of the game for which an IGN needs to be displayed.
            Displays all the stored IGNs if not specified.
        """
        member = user or ctx.author
        oneself = ctx.author == member
        if ctx.guild:
            color = member.top_role.color
        else:
            color = discord.Color.blurple()

        cursor = self.get_IGNs(member.id)
        if not (igns := cursor.fetchone()):
            if oneself:
                await ctx.reply(self.l10n.format_value(
                        'self-igns-notfound',
                        {'cmd': ctx.clean_prefix + ctx.command.parent.name}))
            else:
                embed = discord.Embed(
                    description=self.l10n.format_value(
                        'other-igns-notfound', {'member': member.mention}),
                    color=color
                )
                await ctx.reply(embed=embed)
            return

        if game:
            try:
                ign = self.bot.c.execute(
                    f'select {game} from ign where Discord_UID = ?',
                    (member.id,)
                ).fetchone()
            except sqlite3.OperationalError:
                content = self.l10n.format_value(
                    'game-notfound',
                    {'game': game, 'cmd': f'{ctx.clean_prefix}{ctx.command.parent}'}
                )
                await ctx.reply(content)
                return
            if ign and ign[0]:
                embed = discord.Embed(description=ign[0], color=color)
                await ctx.reply(embed=embed)
            elif oneself:
                await ctx.reply(self.l10n.format_value(
                        'self-ign-notfound', {'game': game}))
            else:
                embed = discord.Embed(
                    description=self.l10n.format_value(
                        'other-ign-notfound',
                        {'member': member.mention, 'game': game}
                    ),
                    color=color
                )
                await ctx.reply(embed=embed)
            return

        user_igns = []
        for game, ign in zip(cursor.description[1:], igns[1:]):
            if ign:
                user_igns.append(f'**{game[0]}:** {ign}')

        embed = discord.Embed(
            title=self.l10n.format_value(
                'igns-title', {'member': f'{member}'}
            ),
            description='\n'.join(user_igns),
            color=color
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        if not oneself:
            embed.set_footer(
                text=self.l10n.format_value(
                    'request', {'author': f'{ctx.author}'}
                ),
                icon_url=ctx.author.avatar.url
            )

        await ctx.send(embed=embed)

    @ign.command(aliases=['del', 'remove', 'rm'])
    async def delete(self, ctx, *, game: str = None):
        """Delete an IGN for the given game or all games.

        Parameters
        ------------
        `game`: Optional[<class 'str'>]
            The game for which an IGN is to be deleted. It is case \
            insensitive and can only contain a game that has a corresponding \
            IGN for the user.
            If this is left blank, all the stored IGNs are deleted.
        """
        cursor = self.get_IGNs(ctx.author.id)
        if not (igns := cursor.fetchone()):
            await ctx.reply(self.l10n.format_value(
                    'self-igns-notfound',
                    {'cmd': f'{ctx.clean_prefix}{ctx.command.parent}'}))
            return

        if not game:
            self.bot.c.execute(
                'delete from ign where Discord_UID = ?', (ctx.author.id,)
            )
            self.bot.db.commit()
            await ctx.reply(self.l10n.format_value('remove-all-success'))
            return

        if not (game := await self.exists(ctx, game)):
            return

        ign = self.bot.c.execute(
            f'select {game} from ign where Discord_UID = ?', (ctx.author.id,)
        ).fetchone()
        if ign and ign[0]:
            igns = [ign for ign in igns[1:] if ign]
            if len(igns) > 1:
                self.bot.c.execute(
                    f'update ign set {game} = null where Discord_UID = ?',
                    (ctx.author.id,)
                )
            else:
                self.bot.c.execute(
                    'delete from ign where Discord_UID = ?', (ctx.author.id,)
                )
            self.bot.db.commit()
            await ctx.reply(
                self.l10n.format_value('remove-success', {'game': game})
            )
        else:
            await ctx.reply(
                self.l10n.format_value('self-ign-notfound', {'game': game})
            )


def setup(bot):
    """Called when this file is attempted to be loaded as an extension"""
    bot.add_cog(IGN(bot))
