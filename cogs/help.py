import discord
from typing import Optional
from discord.utils import get
from discord.ext import commands

def syntax(command):
    aliases = [str(command), *command.aliases]
    if len(aliases) > 1:
        aliases = '[' + '|'.join(aliases) + ']'
    else:
        aliases = aliases[0]
    if command.parent:
        aliases = aliases.replace(f'{command.parent} ', '')
    params = []

    for key, value in command.params.items():
        if key not in ('self', 'ctx'):
            params.append(f'[{key}]' if 'NoneType' in str(value) else f'<{key}>')
    params = ' '.join(params)

    if not (help := command.help):
        help = command.brief

    return help, aliases, params

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.remove_command('help')

    async def cmd_help(self, ctx, command):
        if command.cog:
            embed = discord.Embed(
                title = f'{command.cog.qualified_name} Help!',
                color = discord.Color.blurple()
            )
            for command in command.cog.walk_commands():
                _, aliases, params = syntax(command)
                if command.parent:
                    field_name = f'{command.parent} {aliases} {params}'
                else:
                    field_name = f'{aliases} {params}'
                if not (help := command.help):
                    help = command.brief
                embed.add_field(name=field_name, value=help, inline=False)
            await ctx.send(embed=embed)
        else:
            help, aliases, params = syntax(command)
            embed = discord.Embed(
                title = f'{command} {params}',
                description = help,
                color = discord.Color.blurple()
            )
            if '|' in aliases:
                aliases = aliases.replace(f'{command}|', '')
                embed.add_field(name='Aliases', value=f'`{aliases}`')
            await ctx.send(embed=embed)

    @commands.command(name='help')
    async def help(self, ctx, cmd: Optional[str]):
        if not cmd:
            embed = discord.Embed(
                title = 'Commands Help!',
                description = f'For help with a specific command, type {ctx.prefix}help <command>',
                color = discord.Color.blurple()
            )
            embed.set_thumbnail(url=self.bot.user.avatar_url)
            for command in self.bot.commands:
                _, aliases, params = syntax(command)
                embed.add_field(name=f'{aliases} {params}', value=command.brief, inline=False)
            await ctx.send(embed=embed)
        else:
            if command := get(self.bot.commands, name=cmd):
                await self.cmd_help(ctx, command)
            else:
                embed = discord.Embed(
                    title = 'Command not found',
                    description = f'Unknown command `{cmd}`',
                    color = discord.Color.from_rgb(255, 165, 0)
                )
                await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Help(bot))
