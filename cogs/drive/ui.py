from __future__ import annotations

from typing import TYPE_CHECKING

from discord import User, Message
from discord.interactions import Interaction
from discord.ui import Select, View

if TYPE_CHECKING:
    from main import ProjectHyperlink


class DriveSearchView(View):
    message: Message

    def __init__(
        self,
        author: User,
        contents: list[str],
        *,
        timeout: float | None = 60,
    ):
        super().__init__(timeout=timeout)
        self.author = author
        self.search_result_select = DriveSearchSelect(self, contents)
        self.add_item(self.search_result_select)

    async def finish_search(self, interaction: Interaction) -> None:
        self.remove_item(self.search_result_select)
        await interaction.message.edit(content="Interaction Finished", view=self)
        self.stop()

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user == self.author:
            return True

        return False


class DriveSearchSelect(Select):
    def __init__(self, parent: DriveSearchView, contents: list[str], **kwargs) -> None:
        super().__init__(**kwargs)
        self.parent = parent
        for i in contents:
            self.add_option(label=i)

    async def callback(self, interaction: Interaction):
        await interaction.response.defer()
        await interaction.followup.send(f"You selected {self.values}", ephemeral=True)
        await self.parent.finish_search(interaction)
