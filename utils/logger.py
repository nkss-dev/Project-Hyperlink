import aiohttp
import asyncio
import logging
import traceback

import config
import discord

# TODO: Add handler for debug which posts into a file.
# Ref: https://github.com/Rapptz/discord.py/blob/master/examples/advanced_startup.py#L67-L72


class InfoHandler(logging.Handler):
    def __init__(self):
        super().__init__(logging.INFO)
        self.max_level = logging.INFO
        self.setFormatter(discord.utils._ColourFormatter())

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno <= self.max_level or config.dev is True:
            # TODO: Take care of `record.extra`
            print(self.format(record))


class ErrorHandler(logging.Handler):
    def __init__(self, loop: asyncio.AbstractEventLoop, session: aiohttp.ClientSession):
        super().__init__(logging.WARNING)
        self.loop = loop
        self.webhook = discord.Webhook.from_url(config.log_url, session=session)
        self.setFormatter(discord.utils._ColourFormatter())

        self.colors = {
            "WARNING": discord.Color.orange(),
            "ERROR": discord.Color.red(),
            "CRITICAL": discord.Color.red(),
        }

        mentions = []
        for owner_id in config.owner_ids:
            mentions.append(f"<@{owner_id}>")
        self.cc = f"cc {', '.join(mentions)}"

    def emit(self, record):
        try:
            embed = discord.Embed(
                title=record.levelname,
                description=record.msg,
                color=self.colors[record.levelname],
            )

            fields: dict[str, str] | None = record.__dict__.get("fields")
            if fields:
                for name, value in fields.items():
                    embed.add_field(name=name, value=value, inline=False)

            if record.exc_info:
                exc_type, exc_value, exc_traceback = record.exc_info
                tb = "".join(
                    traceback.format_exception(exc_type, exc_value, exc_traceback)
                )
                embed.add_field(name="Traceback", value=f"```{tb}```", inline=False)

            user: discord.Member | discord.User | None = record.__dict__.get("user")
            if user is not None:
                embed.add_field(name="Invoked by", value=f"{user.mention}: {user.id}")

            asyncio.run_coroutine_threadsafe(
                self.webhook.send(
                    content=self.cc if record.levelno > logging.WARNING else "",
                    embed=embed,
                    silent=record.levelno < logging.CRITICAL,
                    username="Hyperlink Status",
                ),
                self.loop,
            )
        except:
            raise
