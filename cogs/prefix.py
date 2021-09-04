import json
from utils.l10n import get_l10n

from discord.ext import commands

class Prefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_check(self, ctx):
        self.l10n = get_l10n(ctx.guild.id, 'prefix')
        return self.bot.verificationCheck(ctx)

    @commands.group(brief='Manages the server\'s custom prefixes')
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(manage_guild=True)
    @commands.guild_only()
    async def prefix(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.reply(self.l10n.format_value('invalid-command', {'name': ctx.command.name}))
            return

    @prefix.command(brief='Adds a prefix for this server')
    async def add(self, ctx, prefix):
        prefixes = self.bot.guild_data[str(ctx.guild.id)]['prefix']

        if prefix in prefixes:
            await ctx.reply(self.l10n.format_value('prefix-exists-true', {'prefix': prefix}))
            return

        prefixes.append(prefix)
        self.bot.guild_data[str(ctx.guild.id)]['prefix'] = prefixes
        self.save()

        await ctx.reply(self.l10n.format_value('add-success', {'prefix': prefix}))

    @prefix.command(brief='Removes a prefix from the server')
    async def remove(self, ctx, prefix):
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

    @prefix.command(brief='Removes all custom prefixes and sets to the specified prefix')
    async def set(self, ctx, prefix):
        self.bot.guild_data[str(ctx.guild.id)]['prefix'] = [prefix]
        self.save()

        await ctx.reply(self.l10n.format_value('guild-prefix', {'prefix': prefix}))

    def save(self):
        with open('db/guilds.json', 'w') as f:
            json.dump(self.bot.guild_data, f)

def setup(bot):
    bot.add_cog(Prefix(bot))
