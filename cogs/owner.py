import json
from utils.l10n import get_l10n

from discord.ext import commands

class OwnerOnly(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open('db/emojis.json', 'r') as f:
            self.emojis = json.load(f)['utility']

    async def cog_check(self, ctx):
        return await commands.is_owner().predicate(ctx)

    @commands.command(brief='Loads a cog')
    async def load(self, ctx, extension):
        await ctx.message.add_reaction(self.emojis['loading'])

        self.bot.load_extension(f'cogs.{extension}')

        l10n = get_l10n(ctx.guild.id, 'owner')
        await ctx.send(l10n.format_value('load-successful', {'ext': extension}))

        await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)

    @commands.command(brief='Unloads a cog')
    async def unload(self, ctx, extension):
        await ctx.message.add_reaction(self.emojis['loading'])

        self.bot.unload_extension(f'cogs.{extension}')

        l10n = get_l10n(ctx.guild.id, 'owner')
        await ctx.send(l10n.format_value('unload-successful', {'ext': extension}))

        await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)

    @commands.command(brief='Reloads a cog')
    async def reload(self, ctx, extension):
        await ctx.message.add_reaction(self.emojis['loading'])

        self.bot.unload_extension(f'cogs.{extension}')
        self.bot.load_extension(f'cogs.{extension}')

        l10n = get_l10n(ctx.guild.id, 'owner')
        await ctx.send(l10n.format_value('reload-successful', {'ext': extension}))

        await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)

    @commands.command(brief='Restarts the bot')
    async def restart(self, ctx):
        await ctx.message.delete()
        await self.bot.close()

def setup(bot):
    bot.add_cog(OwnerOnly(bot))
