import discord, sqlite3, json
from discord.ext import commands

class Prefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

        with open('db/guilds.json') as f:
            self.data = json.load(f)

    async def cog_check(self, ctx):
        return self.bot.verificationCheck(ctx)

    @commands.group(name='prefix', brief='Manages the server\'s custom prefixes', invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    @commands.bot_has_permissions(manage_guild=True)
    async def prefix(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.reply('Invalid prefix command passed.')
            return

    @prefix.command(name='add', brief='Adds a prefix for this server')
    async def add(self, ctx, prefix):
        prefixes = self.data[str(ctx.guild.id)]['prefix']
        if prefix in prefixes:
            await ctx.reply(f'{prefix} already exists!')
            return
        prefixes.append(prefix)
        self.data[str(ctx.guild.id)]['prefix'] = prefixes
        self.save()
        await ctx.send(f'{prefix} added')

    @prefix.command(name='remove', brief='Removes a prefix from the server')
    async def remove(self, ctx, prefix):
        prefixes = self.data[str(ctx.guild.id)]['prefix']
        if prefix not in prefixes:
            await ctx.reply(f'{prefix} does not exist!')
            return
        prefixes.remove(prefix)
        self.data[str(ctx.guild.id)]['prefix'] = prefixes
        self.save()
        await ctx.send(f'{prefix} removed')

    @prefix.command(name='clear', brief='Removes all prefixes')
    async def clear(self, ctx):
        self.data[str(ctx.guild.id)]['prefix'] = []
        self.save()
        await ctx.send(f'All prefixes have been removed')

    @prefix.command(name='set', brief='Removes all custom prefixes and sets to the specified prefix')
    async def set(self, ctx, prefix):
        self.data[str(ctx.guild.id)]['prefix'] = [prefix]
        self.save()
        await ctx.send(f'Prefix for this server is now {prefix}')

    def save(self):
        with open('db/guilds.json', 'w') as f:
            json.dump(self.data, f)

def setup(bot):
    bot.add_cog(Prefix(bot))
