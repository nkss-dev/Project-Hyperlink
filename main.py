import config
import re
import traceback

import discord
from discord.ext import commands

from utils.constructor import Constructor

initial_extensions = (
    'cogs.check',
    'cogs.drive',
    'cogs.events',
    'cogs.help',
    'cogs.ign',
    'cogs.info',
    'cogs.links',
    'cogs.logger',
    'cogs.mod',
    'cogs.owner',
    'cogs.prefix',
    'cogs.self_roles',
    'cogs.tag',
    'cogs.verification',
    'cogs.VoiceChat',
    'cogs.voltorb',
)


class ProjectHyperlink(commands.Bot):
    """A Discord bot for servers based around NITKKR"""

    def __init__(self):
        intents = discord.Intents(
            guilds=True,
            members=True,
            bans=True,
            emojis=True,
            voice_states=True,
            messages=True,
            reactions=True
        )
        super().__init__(
            command_prefix=self._prefix_callable,
            intents=intents,
            owner_ids=config.owner_ids
        )

        self.loop.create_task(self.construct())

    @staticmethod
    def _prefix_callable(bot, msg) -> list:
        """Return the bot's prefix for a guild or a DM"""
        base = []
        if not msg.guild:
            base.append('%')
        else:
            base.extend(bot.guild_data[str(msg.guild.id)]['prefix'])
        return base

    async def construct(self):
        """Setup all initial requirements"""
        await self.wait_until_ready()
        Constructor(self)

        # Load all the extensions
        for extension in initial_extensions:
            try:
                self.load_extension(extension)
            except Exception:
                print(f'\nFailed to load extension {extension}.\n')
                traceback.print_exc()

    def run(self):
        super().run(config.bot_token, reconnect=True)


if __name__ == '__main__':
    bot = ProjectHyperlink()

    @bot.before_invoke
    async def bracketCheck(ctx):
        """Raise an error if any argument is enclosed in angular brackets"""
        if re.search(r'<[^#@].+>', ctx.message.content):
            raise commands.CheckFailure('AngularBracketsNotAllowed')

    bot.run()
