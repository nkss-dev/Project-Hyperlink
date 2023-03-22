import aiohttp
import asyncio
import logging
import re
import sys
import traceback
from aiohttp import web

import asyncpg
import config
import discord
from discord.ext import commands
from fluent.runtime import FluentLocalization, FluentResourceLoader

from api.main import app
from utils.logger import BotLogHandler

initial_extensions = (
    'cogs.verification.verification',
    'cogs.drive',
    'cogs.errors',
    'cogs.events',
    'cogs.help',
    'cogs.ign',
    'cogs.info',
    'cogs.logger',
    'cogs.mod',
    'cogs.owner',
    'cogs.prefix',
    'cogs.self_roles',
    'cogs.tag',
    'cogs.VoiceChat',
    'cogs.voltorb',
)

loader = FluentResourceLoader('l10n/{locale}')


class ProjectHyperlink(commands.Bot):
    """A personal moderation bot made as a part of the NKSSS project"""

    pool: asyncpg.Pool
    session: aiohttp.ClientSession
    locales: dict[int, str] = {}
    l10n: dict[str, FluentLocalization] = {}

    def __init__(self):
        intents = discord.Intents(
            bans=True,
            emojis=True,
            guilds=True,
            members=True,
            messages=True,
            message_content=True,
            reactions=True,
            voice_states=True
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
            prefixes = await bot.pool.fetch(
                'SELECT prefix FROM bot_prefix WHERE guild_id = $1',
                msg.guild.id
            )
            if prefixes:
                prefixes = [prefix['prefix'] for prefix in prefixes]
            else:
                prefixes = ['%']
            base.extend(prefixes)
        return base

    async def get_l10n(self, id: int = 0) -> FluentLocalization:
        if not self.locales.get(id):
            self.locales[id] = await self.pool.fetchval(
                'SELECT locale FROM guild WHERE id = $1', id
            ) or 'en-GB'
        locale = self.locales[id]

        if not self.l10n.get(locale):
            files = map(lambda file: f"{file.split('.')[-1]}.ftl", initial_extensions)
            self.l10n[locale] = FluentLocalization([locale], files, loader)
        return self.l10n[locale]

    async def on_ready(self):
        if not hasattr(self, 'launch_time'):
            self.launch_time = discord.utils.utcnow()

        print(f'Logged in as {self.user} (ID: {self.user.id})')

    async def setup_hook(self):
        # Launch the API
        app['bot'] = self
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, 'localhost', 8080)
        await site.start()
        print('API launched successfully!')

    async def close(self) -> None:
        await self.session.close()
        await asyncio.wait_for(self.pool.close(), timeout=None)
        await super().close()


async def main():
    async with ProjectHyperlink() as bot:
        bot.logger = logging.getLogger("BotLogger")
        bot.logger.addHandler(BotLogHandler(bot, 1086928165303234680))

        try:
            pool = await asyncpg.create_pool(
                dsn=config.dsn,
                command_timeout=60,
                max_inactive_connection_lifetime=0
            )
        except Exception:
            raise

        if pool is None:
            raise RuntimeError('Could not connect to the database')
        bot.pool = pool

        session = aiohttp.ClientSession()
        bot.session = session

        # !TODO: Setup logging
        for extension in initial_extensions:
            try:
                await bot.load_extension(extension)
            except Exception:
                print(
                    '\33[91m'
                    + f'\nFailed to load extension {extension}.\n'
                    + '\33[93m'
                    + traceback.format_exc()
                    + '\33[0m',
                    file=sys.stderr
                )

        @bot.check_once
        async def bracketCheck(ctx):
            """Raise an error if any argument is enclosed in angular brackets"""
            if re.search(r'<[^#@a:].+>', ctx.message.content):
                raise commands.CheckFailure('AngularBracketsNotAllowed')
            return True
        
        await bot.start(config.bot_token)

if __name__ == '__main__':
    asyncio.run(main())
