import asyncio
import logging
import traceback

import discord


class BotLogHandler(logging.Handler):
    def __init__(self, bot, channel_id, level=logging.DEBUG):
        super().__init__(level)
        self.bot = bot
        self.channel_id = channel_id

        self.colors = {
            "VERBOSE": discord.Color.blurple(),
            "DEBUG": discord.Color.blurple(),
            "INFO": discord.Color.blurple(),
            "WARNING": discord.Color.orange(),
            "ERROR": discord.Color.red(),
            "EXCEPTION": discord.Color.red(),
            "CRITICAL": discord.Color.red(),
            "LOG": discord.Color.blurple(),
            "_LOG": discord.Color.blurple(),
        }

    def emit(self, record):
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

            channel = self.bot.get_channel(self.channel_id)
            asyncio.run_coroutine_threadsafe(channel.send(embed=embed), self.bot.loop)
        except:
            raise
