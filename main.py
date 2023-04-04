import asyncio
import logging
import pathlib
import os
from typing import Any, Type
from aiohttp import ClientSession, web

import asyncpg
import config
import discord
from discord.ext import commands
from fluent.runtime import FluentLocalization, FluentResourceLoader

import cogs
from api.main import app
from base.context import HyperlinkContext
from cogs.verification.ui import VerificationView
from utils.logger import ErrorHandler, InfoHandler


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
            emojis=True,
            guilds=True,
            members=True,
            messages=True,
            message_content=True,
            moderation=True,
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
        self._l10n_path = "l10n/{locale}"
        self._l10n: dict[str, FluentLocalization] = {}
        self._loader = FluentResourceLoader(self._l10n_path)
        self._guild_locales = {0: "en-GB"}

        self.pool = db_pool
        self.launch_time = discord.utils.utcnow()
        self.logger = logger
        self.session = web_client

    @staticmethod
    async def _prefix_callable(bot, message: discord.Message) -> list:
        """Return the bot's prefix for a guild or a DM"""
        await bot.wait_until_ready()

        if config.dev is True:
            DEFAULT_PREFIX = "!"
        else:
            DEFAULT_PREFIX = "%"

        prefixes = [DEFAULT_PREFIX]

        if message.guild is None:
            return prefixes

        saved_prefixes = await bot.pool.fetch(
            "SELECT prefix FROM bot_prefix WHERE guild_id = $1",
            message.guild.id,
        )
        if saved_prefixes:
            prefixes = [prefix["prefix"] for prefix in saved_prefixes]

        return prefixes

    async def get_context(
        self,
        origin: discord.Message | discord.Interaction,
        /,
        *,
        cls: Type = None,
    ) -> Any:
        return await super().get_context(origin, cls=cls or HyperlinkContext)

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
            path = pathlib.Path(self._loader.localize_path(self._l10n_path, locale))
            files = [f.name for f in path.iterdir() if f.is_file()]
            self._l10n[locale] = FluentLocalization([locale], files, self._loader)

        return self._l10n[locale]

    async def on_ready(self):
        assert self.user is not None
        self.logger.info(f"Logged in as {self.user} (ID: {self.user.id})")

    async def setup_hook(self) -> None:
        results = await asyncio.gather(
            *(self.load_extension(ext) for ext in cogs.INITIAL_EXTENSIONS),
            return_exceptions=True,
        )
        for ext, result in zip(cogs.INITIAL_EXTENSIONS, results):
            if isinstance(result, Exception):
                self.logger.error(f"Failed to load extension `{ext}`: {result}")

        l10n = await self.get_l10n(0)
        self.add_view(VerificationView(l10n.format_value("verify-button-label")))

        # Launch the API
        app["bot"] = self
        runner = web.AppRunner(app)
        await runner.setup()

        port = int(os.environ.get("PORT") or 8080)
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        self.logger.info(f"API running at localhost:{port}")


async def main():
    logger = logging.getLogger("ProjectHyperlink")
    logger.setLevel(logging.DEBUG)
    logger.addHandler(InfoHandler())

    discord.utils.setup_logging(level=logging.INFO, root=False)

    pool = asyncpg.create_pool(
        dsn=config.dsn, command_timeout=60, max_inactive_connection_lifetime=0
    )
    session = ClientSession()
    bot = ProjectHyperlink(
        db_pool=pool,
        logger=logger,
        web_client=session,
    )

    if config.dev is False:
        LOGGING_CHANNEL_ID: int = 1086928165303234680
        logger.addHandler(ErrorHandler(bot, LOGGING_CHANNEL_ID))

    async with session, pool, bot:
        if config.dev is True:
            await bot.start(config.dev_bot_token)
        else:
            await bot.start(config.bot_token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
