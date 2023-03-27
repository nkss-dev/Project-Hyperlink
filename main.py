import asyncio
import logging
import pathlib
import os
from aiohttp import ClientSession, web

import asyncpg
import config
import discord
from discord.ext import commands
from fluent.runtime import FluentLocalization, FluentResourceLoader

import cogs
from api.main import app
from cogs.verification.ui import VerificationView
from utils.logger import ErrorHandler, Logger


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
            path = pathlib.Path(self._loader.localize_path(self._l10n_path, locale))
            files = [f.name for f in path.iterdir() if f.is_file()]
            self._l10n[locale] = FluentLocalization([locale], files, self._loader)

        return self._l10n[locale]

    async def on_ready(self):
        assert self.user is not None
        self.logger.info(f"Logged in as {self.user} (ID: {self.user.id})")

    async def setup_hook(self) -> None:
        for extension in cogs.INITIAL_EXTENSIONS:
            try:
                await self.load_extension(extension)
            except Exception:
                self.logger.exception(f"Failed to load extension `{extension}`")

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
    logger = Logger()
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

    LOGGING_CHANNEL_ID: int = 1086928165303234680
    logger.addHandler(ErrorHandler(bot, LOGGING_CHANNEL_ID))

    async with session, pool, bot:
        await bot.start(config.bot_token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
