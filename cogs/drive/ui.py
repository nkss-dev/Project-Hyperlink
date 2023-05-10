from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.colour import Colour
from discord.enums import ButtonStyle

if TYPE_CHECKING:
    from main import ProjectHyperlink


class DriveSearchView(discord.ui.View):
    def __init__(
        self,
        author: discord.Member | discord.User,
        *,
        timeout: float | None = 60,
    ):
        """UI for interacting with the search results

        Args:
            author: User who invoked the command
            contents: Paginated list of search results. All results in a page\
                are assumed to be a joined together to form a single `str`.
            embed (Embed): The embed that contains the results
            timeout (float | None, optional): _description_. Defaults to 60.
        """
        super().__init__(timeout=timeout)
        self.author = author
        self.current_page = 0
        self.message: discord.Message | None = None
        self.last_found = False  # set to true once API returns last page

        # TODO: send API call for first page
        self.pages = [ResultEmbed(description="This is a test description")]

    async def on_timeout(self):
        if self.message:
            await self.message.edit(view=None)
        return await super().on_timeout()

    async def interaction_check(
        self, interaction: discord.Interaction[ProjectHyperlink]
    ) -> bool:
        if interaction.user == self.author:
            return True
        return False

    async def on_page_change(
        self, interaction: discord.Interaction[ProjectHyperlink], page: int
    ) -> None:
        # TODO: somehow delete this once embed is edited. if not possible, don't send this
        await interaction.response.defer(ephemeral=True, thinking=True)

        self.current_page = page
        try:
            self.pages[page]
        except IndexError:
            # TODO: send API call for new page
            self.pages.append(ResultEmbed(description=f"Page {page}"))

        is_first_page = page == 0
        is_last_page = self.last_found and page == (len(self.pages) - 1)

        self.first_page_button.disabled = is_first_page
        self.previous_page_button.disabled = is_first_page
        self.page_button.label = str(page)
        self.next_page_button.disabled = is_last_page
        self.last_page_button.disabled = is_last_page

        assert self.message is not None
        await self.message.edit(embed=self.pages[page], view=self)

    @discord.ui.button(label="<<", style=ButtonStyle.green, disabled=True, row=0)
    async def first_page_button(
        self, interaction: discord.Interaction[ProjectHyperlink], _: discord.ui.Button
    ) -> None:
        await self.on_page_change(interaction, 0)

    @discord.ui.button(label="Previous", style=ButtonStyle.green, disabled=True, row=0)
    async def previous_page_button(
        self, interaction: discord.Interaction[ProjectHyperlink], _: discord.ui.Button
    ) -> None:
        await self.on_page_change(interaction, max(self.current_page - 1, 0))

    @discord.ui.button(label="0", style=ButtonStyle.gray, disabled=True, row=0)
    async def page_button(
        self, interaction: discord.Interaction[ProjectHyperlink], _: discord.ui.Button
    ):
        pass

    @discord.ui.button(label="Next", style=ButtonStyle.green, row=0)
    async def next_page_button(
        self, interaction: discord.Interaction[ProjectHyperlink], _: discord.ui.Button
    ) -> None:
        await self.on_page_change(interaction, self.current_page + 1)

    @discord.ui.button(label=">>", style=ButtonStyle.green, row=0)
    async def last_page_button(
        self, interaction: discord.Interaction[ProjectHyperlink], _: discord.ui.Button
    ) -> None:
        await self.on_page_change(interaction, len(self.pages) - 1)


class ResultEmbed(discord.Embed):
    """Embed that displays search results"""

    def __init__(
        self,
        description: str,
        color: int | Colour | None = Colour.blurple(),
        **kwargs,
    ):
        super().__init__(
            title="Results", description=description, color=color, **kwargs
        )


class DriveSearchSelect(discord.ui.Select):
    def __init__(self, parent: DriveSearchView, contents: list[str], **kwargs) -> None:
        super().__init__(**kwargs)
        self.parent = parent
        for i in contents:
            self.add_option(label=i)

    async def callback(self, interaction: discord.Interaction[ProjectHyperlink]):
        await interaction.response.defer()
        await interaction.followup.send(f"You selected {self.values}", ephemeral=True)
        # await self.parent.finish_search(interaction)
