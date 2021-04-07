import discord, sqlite3, json
from discord.ext import commands

class Prefix(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

        try:
            with open('db/guilds.json') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {}

    @commands.group(name='prefix', brief='Manages the server\'s custom prefixes', invoke_without_command=True)
    async def prefix(self, ctx):
        """Manages the server's custom prefixes.
        If called without a subcommand, this will list the currently set
        prefixes."""
        prefixes = self.data[str(ctx.guild.id)]['prefix']
        embed = discord.Embed(
            title = 'Prefixes',
            description = ',\n'.join([f'{prefix[0] + 1}. {prefix[1]}' for prefix in enumerate(prefixes)]),
            color = discord.Color.blurple()
        )
        await ctx.send(embed=embed)

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
