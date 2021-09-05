import contextlib
from discord import Color, Embed, utils
from discord.ext import commands

from utils.l10n import get_l10n

class HelpEmbed(Embed):
    def __init__(self, l10n, **kwargs):
        super().__init__(**kwargs)
        self.timestamp = utils.utcnow()
        self.set_footer(text=l10n.format_value('footer'))
        self.color = Color.blurple()

class Help(commands.HelpCommand):
    def __init__(self):
        super().__init__(
            command_attrs={
                'help': 'The help command for the bot',
                'cooldown': commands.CooldownMapping.from_cooldown(2, 5.0, commands.BucketType.user),
                'aliases': ['commands']
            }
        )

    async def send(self, **kwargs):
        """a shortcut to sending to get_destination"""
        await self.get_destination().send(**kwargs)

    async def send_bot_help(self, mapping):
        """invoked when `<prefix>help` is called"""
        l10n = get_l10n(self.context.guild.id if self.context.guild else 0, 'help')
        bot = self.context.me
        prefix = self.context.clean_prefix

        embed = HelpEmbed(l10n, title=l10n.format_value('help-title', {'name': bot.name}))
        embed.set_thumbnail(url=bot.avatar.url)
        total = 0
        usable = 0

        for cog, commands in mapping.items():
            total += len(commands)
            if filtered_commands := await self.filter_commands(commands):
                amount = len(filtered_commands)
                usable += amount
                if cog:
                    name = cog.qualified_name
                    description = cog.description or l10n.format_value('desc-notfound')
                else:
                    for command in commands:
                        print(command)
                    name = l10n.format_value('category-notfound')
                    description = l10n.format_value('no-category-commands')

                embed.add_field(
                    name=l10n.format_value('category-title', {'name': name, 'amt': amount}),
                    value=description
                )

        embed.description = l10n.format_value('help-desc', {'total': total, 'amt': usable})

        await self.send(embed=embed)

    async def send_command_help(self, command):
        l10n = get_l10n(self.context.guild.id if self.context.guild else 0, 'help')
        prefix = self.context.clean_prefix

        embed = HelpEmbed(l10n, title=self.get_command_signature(command))
        embed.add_field(
            name=l10n.format_value('help'),
            value=command.help or command.brief,
            inline=False
        )

        if cog := command.cog:
            embed.add_field(name=l10n.format_value('category'), value=cog.qualified_name)

        with contextlib.suppress(commands.CommandError):
            usable = await command.can_run(self.context)
        embed.add_field(
            name=l10n.format_value('usable'),
            value=l10n.format_value('yes') if usable else l10n.format_value('no')
        )

        if command._buckets and (cooldown := command._buckets._cooldown):
            embed.add_field(
                name=l10n.format_value('cooldown'),
                value=l10n.format_value(
                    'cooldown-value',
                    {'rate': cooldown.rate, 'per': str(cooldown.per).split('.', 1)[0]}
                )
            )

        if alias := command.aliases:
            embed.add_field(
                name=l10n.format_value('aliases'),
                value=', '.join(alias)
            )

        await self.send(embed=embed)

    async def send_help_embed(self, title, description, commands):
        """helper function to add commands to an embed and send it"""
        l10n = get_l10n(self.context.guild.id if self.context.guild else 0, 'help')
        embed = HelpEmbed(
            l10n,
            title=title,
            description=description or l10n.format_value('help-notfound')
        )

        if filtered_commands := await self.filter_commands(commands):
            for command in filtered_commands:
                embed.add_field(
                    name=self.get_command_signature(command),
                    value=command.brief or command.help or l10n.format_value('help-notfound'),
                    inline=False
                )

        await self.send(embed=embed)

    async def send_group_help(self, group):
        """invoked when `<prefix>help <group>` is called"""
        title = self.get_command_signature(group)
        await self.send_help_embed(title, group.help, group.commands)

    async def send_cog_help(self, cog):
        """invoked when `<prefix>help <cog>` is called"""
        l10n = get_l10n(self.context.guild.id if self.context.guild else 0, 'help')
        title = cog.qualified_name or l10n.format_value('category-notfound')
        await self.send_help_embed(title, cog.description, cog.get_commands())

def setup(bot):
    bot.help_command = Help()
