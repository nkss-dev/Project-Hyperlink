from discord.ext import commands

from base.cog import HyperlinkCog
from base.context import HyperlinkContext
import cogs.checks as checks
from main import ProjectHyperlink


class Prefix(HyperlinkCog):
    """Bot prefix management"""

    async def cog_check(self, ctx: commands.Context[ProjectHyperlink]):
        return await checks._is_verified(ctx)

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
    async def prefix(self, ctx: HyperlinkContext):
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
            await ctx.reply("exists-true", l10n_context=dict(prefix=prefix))
            return

        await self.bot.pool.execute(
            "INSERT INTO bot_prefix VALUES ($1, $2)", ctx.guild.id, prefix
        )

        await ctx.reply("add-success", l10n_context=dict(prefix=prefix))

    @prefix.command()
    async def remove(self, ctx: HyperlinkContext, prefix: str):
        """Remove a prefix for the server."""
        """
        Paramters
        -----------
        `prefix`: <class 'str'>
            The prefix to remove.
        """
        prefixes = await self.fetch_prefix(ctx.guild.id)

        if prefix not in prefixes:
            await ctx.reply("exists-false", l10n_context=dict(prefix=prefix))
            return

        await self.bot.pool.execute(
            "DELETE FROM bot_prefix WHERE guild_id = $1 AND prefix = $2",
            ctx.guild.id,
            prefix,
        )

        await ctx.reply("remove-success", l10n_context=dict(prefix=prefix))

    @prefix.command()
    async def set(self, ctx: HyperlinkContext, prefix: str):
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

        await ctx.reply("guild-prefix", l10n_context=dict(prefix=prefix))


async def setup(bot):
    await bot.add_cog(Prefix(bot))
