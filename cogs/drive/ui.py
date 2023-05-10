from __future__ import annotations

from typing import TYPE_CHECKING

from discord import User, Embed
from discord.colour import Colour
from discord.enums import ButtonStyle
from discord.interactions import Interaction
from discord.ui import button, Button, Select, View


if TYPE_CHECKING:
    from main import ProjectHyperlink


class DriveSearchView(View):
    def __init__(
        self,
        author: User,
        contents: list[str],
        embed: Embed,
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
        self.contents = contents
        self.embed = embed
        self.page = 0
        self.page_display_button.label = f"{self.page+1}/{len(self.contents)}"

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user == self.author:
            return True
        return False

    @button(label="<<", style=ButtonStyle.green, disabled=True, row=0)
    async def first_page_button(self, interaction: Interaction, _: Button) -> None:
        self.page = 0
        self.page_display_button.label = f"{self.page+1}/{len(self.contents)}"

        self.first_page_button.disabled = True
        self.previous_page_button.disabled = True
        self.next_page_button.disabled = False
        self.last_page_button.disabled = False

        self.embed.description = self.contents[self.page]
        await interaction.response.edit_message(embed=self.embed, view=self)

    @button(label="Previous", style=ButtonStyle.green, disabled=True, row=0)
    async def previous_page_button(self, interaction: Interaction, _: Button) -> None:
        self.page = max(self.page - 1, 0)
        self.page_display_button.label = f"{self.page+1}/{len(self.contents)}"

        if self.page == 0:
            self.previous_page_button.disabled = True
            self.first_page_button.disabled = True
        else:
            self.next_page_button.disabled = False
            self.last_page_button.disabled = False

        self.embed.description = self.contents[self.page]
        await interaction.response.edit_message(embed=self.embed, view=self)

    @button(label="foo", style=ButtonStyle.gray, disabled=True, row=0)
    async def page_display_button(self, interaction: Interaction, _: Button) -> None:
        pass

    @button(label="Next", style=ButtonStyle.green, row=0)
    async def next_page_button(self, interaction: Interaction, _: Button) -> None:
        self.page = min(self.page + 1, len(self.contents) - 1)
        self.page_display_button.label = f"{self.page+1}/{len(self.contents)}"

        if self.page == (len(self.contents) - 1):
            self.next_page_button.disabled = True
            self.last_page_button.disabled = True
        else:
            self.previous_page_button.disabled = False
            self.first_page_button.disabled = False

        self.embed.description = self.contents[self.page]
        await interaction.response.edit_message(embed=self.embed, view=self)

    @button(label=">>", style=ButtonStyle.green, row=0)
    async def last_page_button(self, interaction: Interaction, _: Button) -> None:
        self.page = len(self.contents) - 1
        self.page_display_button.label = f"{self.page+1}/{len(self.contents)}"

        self.previous_page_button.disabled = False
        self.first_page_button.disabled = False
        self.next_page_button.disabled = True
        self.last_page_button.disabled = True

        self.embed.description = self.contents[self.page]
        await interaction.response.edit_message(embed=self.embed, view=self)

    @button(label="STOP", style=ButtonStyle.danger)
    async def stop_button(self, interaction: Interaction, _: Button) -> None:
        await interaction.response.defer()
        self.stop()


class PageDisplayButton(Button):
    """Button to hold the page number"""

    def __init__(self, label: str, *, row: int | None = 0):
        super().__init__(label=label, row=row, style=ButtonStyle.gray, disabled=True)


class DriveSearchResultEmbed(Embed):
    """Embed that displays search results"""

    def __init__(
        self,
        title: str,
        description: str,
        color: int | Colour | None = Colour.blurple(),
        **kwargs,
    ):
        super().__init__(title=title, description=description, color=color, **kwargs)


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
