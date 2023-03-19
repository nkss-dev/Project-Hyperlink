import asyncio
import logging


class BotLogHandler(logging.Handler):
    def __init__(self, bot, channel_id, level=logging.DEBUG):
        super().__init__(level)
        self.bot = bot
        self.channel_id = channel_id

        formatter = logging.Formatter("**%(levelname)s** %(message)s")
        self.setFormatter(formatter)

    def emit(self, record):
        try:
            msg = self.format(record)
            channel = self.bot.get_channel(self.channel_id)
            asyncio.run_coroutine_threadsafe(channel.send(msg), self.bot.loop)
        except:
            raise
