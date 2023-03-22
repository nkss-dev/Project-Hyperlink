from discord.ext import commands

from utils import checks


class Prefix(commands.Cog):
    """Bot prefix management"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        l10n = await self.bot.get_l10n(ctx.guild.id if ctx.guild else 0)
        self.fmv = l10n.format_value
        return await checks.is_verified().predicate(ctx)

    async def fetch_prefix(self, id: int) -> map:
        return map(
            lambda prefix: prefix["prefix"],
            await self.bot.pool.fetch(
                "SELECT prefix FROM bot_prefix WHERE guild_id = $1", id
            ),
        )

    @commands.group(invoke_without_command=True)
    @commands.bot_has_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def prefix(self, ctx):
        """Command group for bot prefix functionality"""
        await ctx.send_help(ctx.command)

    @prefix.command()
    async def add(self, ctx, prefix: str):
        """Add a prefix for the server."""
        """
        Paramters
        -----------
        `prefix`: <class 'str'>
            The prefix to add.
        """
        prefixes = await self.fetch_prefix(ctx.guild.id)

        if prefix in prefixes:
            await ctx.reply(self.fmv("exists-true", {"prefix": prefix}))
            return

        await self.bot.pool.execute(
            "INSERT INTO bot_prefix VALUES ($1, $2)", ctx.guild.id, prefix
        )

        await ctx.reply(self.fmv("add-success", {"prefix": prefix}))

    @prefix.command()
    async def remove(self, ctx, prefix: str):
        """Remove a prefix for the server."""
        """
        Paramters
        -----------
        `prefix`: <class 'str'>
            The prefix to remove.
        """
        prefixes = await self.fetch_prefix(ctx.guild.id)

        if prefix not in prefixes:
            await ctx.reply(self.fmv("exists-false", {"prefix": prefix}))
            return

        await self.bot.pool.execute(
            "DELETE FROM bot_prefix WHERE guild_id = $1 AND prefix = $2",
            ctx.guild.id,
            prefix,
        )

        await ctx.reply(self.fmv("remove-success", {"prefix": prefix}))

    @prefix.command()
    async def set(self, ctx, prefix: str):
        """Remove all prefixes and set to the specified prefix.

        Paramters
        -----------
        `prefix`: <class 'str'>
            The prefix to set.
        """
        await self.bot.pool.execute(
            "DELETE FROM bot_prefix WHERE guild_id = $1", ctx.guild.id
        )
        await self.bot.pool.execute(
            "INSERT INTO prefix VALUES ($1, $2)", ctx.guild.id, prefix
        )

        await ctx.reply(self.fmv("guild-prefix", {"prefix": prefix}))


async def setup(bot):
    await bot.add_cog(Prefix(bot))
