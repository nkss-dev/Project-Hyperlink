import asyncio
import logging
import os
import traceback
from aiohttp import ClientSession, web
from datetime import datetime

import asyncpg
import config
import discord
from discord.ext import commands
from fluent.runtime import FluentLocalization, FluentResourceLoader

from api.main import app
from utils.logger import ErrorHandler

initial_extensions = [
    "cogs.verification.verification",
    "cogs.drive",
    "cogs.errors",
    "cogs.events",
    "cogs.help",
    "cogs.ign",
    "cogs.info",
    "cogs.logger",
    "cogs.mod",
    "cogs.owner",
    "cogs.prefix",
    "cogs.self_roles",
    "cogs.tag",
    "cogs.verification",
    "cogs.VoiceChat",
    "cogs.voltorb",
]

loader = FluentResourceLoader("l10n/{locale}")


class ProjectHyperlink(commands.Bot):
    """A personal moderation bot made as a part of the NKSSS project"""

    def __init__(
        self,
        *args,
        db_pool: asyncpg.Pool,
        logger: logging.Logger,
        web_client: ClientSession,
        **kwargs,
    ):
        intents = discord.Intents(
            bans=True,
            emojis=True,
            guilds=True,
            members=True,
            messages=True,
            message_content=True,
            reactions=True,
            voice_states=True,
        )
        super().__init__(
            *args,
            **kwargs,
            command_prefix=self._prefix_callable,
            intents=intents,
            owner_ids=config.owner_ids,
        )
        self._l10n: dict[str, FluentLocalization] = {}
        self._guild_locales = {0: "en-GB"}

        self.pool = db_pool
        self.initial_extensions = initial_extensions
        self.launch_time: datetime
        self.logger = logger
        self.session = web_client

    @staticmethod
    async def _prefix_callable(bot, msg: discord.Message) -> list:
        """Return the bot's prefix for a guild or a DM"""
        await bot.wait_until_ready()
        base = []
        if not msg.guild:
            base.append("%")
        else:
            prefixes = await bot.pool.fetch(
                "SELECT prefix FROM bot_prefix WHERE guild_id = $1", msg.guild.id
            )
            if prefixes:
                prefixes = [prefix["prefix"] for prefix in prefixes]
            else:
                prefixes = ["%"]
            base.extend(prefixes)
        return base

    async def get_l10n(self, guild_id: int = 0) -> FluentLocalization:
        if self._guild_locales.get(guild_id) is None:
            self._guild_locales[guild_id] = (
                await self.pool.fetchval(
                    "SELECT locale FROM guild WHERE id = $1", guild_id
                )
                or "en-GB"
            )
        locale = self._guild_locales[guild_id]

        if self._l10n.get(locale) is None:
            # TODO: `files` must not depend on `initial_extensions`
            files = [f"{file.split('.')[-1]}.ftl" for file in initial_extensions]
            self._l10n[locale] = FluentLocalization([locale], files, loader)

        return self._l10n[locale]

    async def on_ready(self):
        logging.info(f"Logged in as {self.user} (ID: {self.user.id})")

    async def setup_hook(self) -> None:
        self.launch_time = discord.utils.utcnow()

        for extension in initial_extensions:
            try:
                await self.load_extension(extension)
            except Exception:
                logging.error(
                    "\33[91m"
                    + f"\nFailed to load extension {extension}.\n"
                    + "\33[93m"
                    + traceback.format_exc()
                    + "\33[0m",
                )

        # Launch the API
        app["bot"] = self
        runner = web.AppRunner(app)
        await runner.setup()

        port = int(os.environ.get("PORT") or 8080)
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        logging.info(f"API running at localhost:{port}!")


async def main():
    logger = logging.getLogger("discord")
    logger.setLevel(logging.DEBUG)

    async with ClientSession() as client, asyncpg.create_pool(
        dsn=config.dsn, command_timeout=60, max_inactive_connection_lifetime=0
    ) as pool:
        async with ProjectHyperlink(
            db_pool=pool,
            logger=logger,
            web_client=client,
        ) as bot:
            logger.addHandler(ErrorHandler(bot, 1086928165303234680))
            discord.utils.setup_logging(level=logging.INFO, root=False)

            await bot.start(config.bot_token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
