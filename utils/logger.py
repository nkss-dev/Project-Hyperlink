import asyncio
import logging
import traceback

import discord


class Logger(logging.Logger):
    def __init__(self):
        super().__init__("discord", logging.DEBUG)
        self.addHandler(InfoHandler())


class InfoHandler(logging.Handler):
    def __init__(self):
        super().__init__(logging.INFO)
        self.max_level = logging.INFO
        self.setFormatter(discord.utils._ColourFormatter())

    def emit(self, record: logging.LogRecord) -> None:
        if record.levelno <= self.max_level:
            print(self.format(record))


class ErrorHandler(logging.Handler):
    def __init__(self, bot, channel_id):
        super().__init__(logging.WARNING)
        self.bot = bot
        self.channel_id = channel_id
        self.setFormatter(discord.utils._ColourFormatter())

        self.colors = {
            "WARNING": discord.Color.orange(),
            "ERROR": discord.Color.red(),
            "CRITICAL": discord.Color.red(),
        }

    def emit(self, record):
        channel = self.bot.get_channel(self.channel_id)
        if channel is None:
            print(self.format(record))
            return

        try:
            embed = discord.Embed(
                title=record.levelname,
                description=record.msg,
                color=self.colors[record.levelname],
            )

            if record.exc_info:
                exc_type, exc_value, exc_traceback = record.exc_info
                tb = "".join(
                    traceback.format_exception(exc_type, exc_value, exc_traceback)
                )
                embed.add_field(name="Traceback", value=f"```{tb}```", inline=False)

            user: discord.Member | discord.User | None = record.__dict__.get("user")
            if user is not None:
                embed.add_field(name="Invoked by", value=f"{user.mention}: {user.id}")

            asyncio.run_coroutine_threadsafe(channel.send(embed=embed), self.bot.loop)
        except:
            raise
