import json
from utils.l10n import get_l10n

from discord.ext import commands

class Prefix(commands.Cog):
    """Bot prefix management"""

    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx) -> bool:
        self.l10n = get_l10n(ctx.guild.id if ctx.guild else 0, 'prefix')
        return self.bot.verificationCheck(ctx)

    @commands.group()
    @commands.bot_has_permissions(manage_guild=True)
    @commands.has_permissions(manage_guild=True)
    @commands.guild_only()
    async def prefix(self, ctx):
        """Command group for bot prefix functionality"""
        if not ctx.invoked_subcommand:
            await ctx.reply(self.l10n.format_value('invalid-command', {'name': ctx.command.name}))
            return

    @prefix.command()
    async def add(self, ctx, prefix: str):
        """Add a prefix for the server

        Paramters
        -----------
        `prefix`: <class 'str'>
            The prefix to add.
        """
        prefixes = self.bot.guild_data[str(ctx.guild.id)]['prefix']

        if prefix in prefixes:
            await ctx.reply(self.l10n.format_value('prefix-exists-true', {'prefix': prefix}))
            return

        prefixes.append(prefix)
        self.bot.guild_data[str(ctx.guild.id)]['prefix'] = prefixes
        self.save()

        await ctx.reply(self.l10n.format_value('add-success', {'prefix': prefix}))

    @prefix.command()
    async def remove(self, ctx, prefix: str):
        """Remove a prefix for the server

        Paramters
        -----------
        `prefix`: <class 'str'>
            The prefix to remove.
        """
        prefixes = self.bot.guild_data[str(ctx.guild.id)]['prefix']

        if prefix not in prefixes:
            await ctx.reply(self.l10n.format_value('prefix-exists-false', {'prefix': prefix}))
            return

        if len(prefixes) == 1:
            await ctx.reply(self.l10n.format_value('atleast-one-required'))
            return

        prefixes.remove(prefix)
        self.bot.guild_data[str(ctx.guild.id)]['prefix'] = prefixes
        self.save()

        await ctx.reply(self.l10n.format_value('remove-success', {'prefix': prefix}))

    @prefix.command()
    async def set(self, ctx, prefix: str):
        """Remove all prefixes and set to the specified prefix

        Paramters
        -----------
        `prefix`: <class 'str'>
            The prefix to set.
        """
        self.bot.guild_data[str(ctx.guild.id)]['prefix'] = [prefix]
        self.save()

        await ctx.reply(self.l10n.format_value('guild-prefix', {'prefix': prefix}))

    def save(self):
        """save the data to a json file"""
        with open('db/guilds.json', 'w') as f:
            json.dump(self.bot.guild_data, f)

def setup(bot):
    """invoked when this file is attempted to be loaded as an extension"""
    bot.add_cog(Prefix(bot))
