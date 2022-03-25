import re
import traceback

import asyncpg
import config
import discord
from discord.ext import commands

initial_extensions = (
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

    @staticmethod
    async def _prefix_callable(bot, msg) -> list:
        """Return the bot's prefix for a guild or a DM"""
        await bot.wait_until_ready()
        base = []
        if not msg.guild:
            base.append('%')
        else:
            prefixes = bot.c.execute(
                'select prefix from prefixes where ID = ?', (msg.guild.id,)
            ).fetchall()
            if prefixes:
                prefixes = [prefix[0] for prefix in prefixes]
            else:
                prefixes = ['%']
            base.extend(prefixes)
        return base

    async def on_ready(self):
        if not hasattr(self, 'launch_time'):
            self.launch_time = discord.utils.utcnow()

        print(f'Logged in as {self.user} (ID: {self.user.id})')

    async def setup_hook(self):
        """Setup all initial requirements"""
        # Setting up the database
        self.conn = await asyncpg.create_pool(
            host=config.postgres.host,
            database=config.postgres.database,
            user=config.postgres.user,
            password=config.postgres.password
        )

        with open('utils/records.sql') as sql:
            await self.conn.execute(sql.read())
        with open('utils/groups.sql') as sql:
            await self.conn.execute(sql.read())
        with open('utils/guilds.sql') as sql:
            await self.conn.execute(sql.read())

        # Load all the extensions
        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
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
        if re.search(r'<[^#@a:].+>', ctx.message.content):
            raise commands.CheckFailure('AngularBracketsNotAllowed')

    bot.run()
