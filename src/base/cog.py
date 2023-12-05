import logging
from typing import Any

from discord.ext import commands

from main import ProjectHyperlink


class HyperlinkCog(commands.Cog):
    """The base cog for all ProjectHyperlink cogs."""

    def __init__(self, bot: ProjectHyperlink, *args: Any, **kwargs: Any) -> None:
        self.bot = bot

        super().__init__(*args, **kwargs)

    @property
    def logger(self):
        return logging.getLogger("ProjectHyperlink")
