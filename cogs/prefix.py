from discord.ext import commands

from utils import checks
from utils.l10n import get_l10n


class Prefix(commands.Cog):
    """Bot prefix management"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        self.l10n = get_l10n(ctx.guild.id if ctx.guild else 0, 'prefix')
        return checks.is_verified()

    @commands.group(invoke_without_command=True)
    @commands.bot_has_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def prefix(self, ctx):
        """Command group for bot prefix functionality"""
        await ctx.send_help(ctx.command)

    @prefix.command()
    async def add(self, ctx, prefix: str):
        """Add a prefix for the server.

        Paramters
        -----------
        `prefix`: <class 'str'>
            The prefix to add.
        """
        prefixes = self.bot.c.execute(
            'select prefix from prefixes where ID = ?', (ctx.guild.id,)
        ).fetchall()

        if prefix in prefixes:
            await ctx.reply(self.l10n.format_value('exists-true', {'prefix': prefix}))
            return

        self.bot.c.execute(
            'insert into prefixes values(?,?)', (ctx.guild.id, prefix,)
        )
        self.bot.db.commit()

        await ctx.reply(self.l10n.format_value('add-success', {'prefix': prefix}))

    @prefix.command()
    async def remove(self, ctx, prefix: str):
        """Remove a prefix for the server.

        Paramters
        -----------
        `prefix`: <class 'str'>
            The prefix to remove.
        """
        prefixes = self.bot.c.execute(
            'select prefix from prefixes where ID = ?', (ctx.guild.id,)
        ).fetchall()

        if (prefix,) not in prefixes:
            await ctx.reply(self.l10n.format_value('exists-false', {'prefix': prefix}))
            return

        self.bot.c.execute(
            'delete from prefixes where ID = ? and prefix = ?',
            (ctx.guild.id, prefix,)
        )
        self.bot.db.commit()

        await ctx.reply(self.l10n.format_value('remove-success', {'prefix': prefix}))

    @prefix.command()
    async def set(self, ctx, prefix: str):
        """Remove all prefixes and set to the specified prefix.

        Paramters
        -----------
        `prefix`: <class 'str'>
            The prefix to set.
        """
        self.bot.c.execute(
            'delete from prefixes where ID = ?', (ctx.guild.id,)
        )
        self.bot.c.execute(
            'insert into prefixes values(?,?)', (ctx.guild.id, prefix,)
        )
        self.bot.db.commit()

        await ctx.reply(self.l10n.format_value('guild-prefix', {'prefix': prefix}))


def setup(bot):
    """Called when this file is attempted to be loaded as an extension"""
    bot.add_cog(Prefix(bot))
