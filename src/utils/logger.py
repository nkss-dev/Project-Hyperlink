import io
import aiohttp
import asyncio
import logging
import traceback

import config
import discord
from discord.ext import tasks

# TODO: Add handler for debug which posts into a file.
# Ref: https://github.com/Rapptz/discord.py/blob/master/examples/advanced_startup.py#L67-L72


class InfoHandler(logging.Handler):
    def __init__(self):
        super().__init__(logging.INFO)
        self.max_level = logging.INFO
        self.setFormatter(discord.utils._ColourFormatter())

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno <= self.max_level or config.TESTING_MODE is True:
            # TODO: Take care of `record.extra`
            print(self.format(record))


class ErrorHandler(logging.Handler):
    def __init__(self, loop: asyncio.AbstractEventLoop, session: aiohttp.ClientSession):
        super().__init__(logging.WARNING)
        self.loop = loop
        self.setFormatter(discord.utils._ColourFormatter())

        assert config.LOG_URL is not None
        self.webhook = discord.Webhook.from_url(config.LOG_URL, session=session)
        self.log_queue = asyncio.Queue()
        self.digest_log_queue.start()

        self.colors = {
            "WARNING": discord.Color.orange(),
            "ERROR": discord.Color.red(),
            "CRITICAL": discord.Color.red(),
        }

        mentions = []
        for owner_id in config.OWNER_IDS:
            mentions.append(f"<@{owner_id}>")
        self.cc = f"cc {', '.join(mentions)}"

    def emit(self, record):
        try:
            embed = discord.Embed(
                title=record.levelname,
                description=record.msg,
                color=self.colors[record.levelname],
            )
            files = []

            fields: dict[str, str] | None = record.__dict__.get("fields")
            if fields:
                for name, value in fields.items():
                    embed.add_field(name=name, value=value, inline=False)

            if record.exc_info:
                exc_type, exc_value, exc_traceback = record.exc_info
                tb = "".join(
                    traceback.format_exception(exc_type, exc_value, exc_traceback)
                )
                if len(f"```{tb}```") > 1024:
                    fp = io.BytesIO(tb.encode("utf-8"))
                    files.append(discord.File(fp, "traceback.txt"))
                else:
                    embed.add_field(name="Traceback", value=f"```{tb}```", inline=False)

            user: discord.Member | discord.User | None = record.__dict__.get("user")
            if user is not None:
                embed.add_field(name="Invoked by", value=f"{user.mention}: {user.id}")

            self.log_queue.put_nowait(
                (
                    record,
                    embed,
                    files,
                )
            )
        except:
            raise

    @tasks.loop(seconds=0)
    async def digest_log_queue(self):
        record, embed, files = await self.log_queue.get()
        await self.webhook.send(
            content=self.cc if record.levelno > logging.WARNING else "",
            embed=embed,
            files=files,
            silent=record.levelno < logging.CRITICAL,
            username="Hyperlink Status",
        )
