from enum import Enum

import discord
from discord.app_commands import Choice, Group

from base.cog import HyperlinkGroupCog
from cogs.drive.ui import DriveSearchView
from main import ProjectHyperlink


class ExamChoice(Enum):
    MID_SEM_1 = 1
    MID_SEM_2 = 2
    MID_SEM_3 = 3
    END_SEM = 4


class Drive(
    HyperlinkGroupCog,
    group_name="drive",
    group_description="All the commands related to NKSS-Drive",
):
    @discord.app_commands.command()
    @discord.app_commands.describe(
        query="The search query for fetching relevant results"
    )
    async def search(
        self, interaction: discord.Interaction[ProjectHyperlink], query: str
    ):
        """Search for the given query and send a corresponding UI."""

        view = DriveSearchView(interaction.user)
        await interaction.response.send_message(embed=view.pages[0], view=view)
        view.message = await interaction.original_response()

    upload = Group(
        name="upload", description="Upload message attachment to the Google Drive."
    )

    @discord.app_commands.command(description="Upload a past paper.")
    @discord.app_commands.choices(
        exam=[  # TODO: probably use an enum for the choices
            Choice(name="Mid Sem - 1", value=ExamChoice.MID_SEM_1.value),
            Choice(name="Mid Sem - 2", value=ExamChoice.MID_SEM_2.value),
            Choice(name="Mid Sem - 3", value=ExamChoice.MID_SEM_3.value),
            Choice(name="End Sem", value=ExamChoice.END_SEM.value),
        ]
    )
    async def past_paper(
        self,
        interaction: discord.Interaction[ProjectHyperlink],
        exam: Choice[int],
        file: discord.Attachment,
        # TODO: add tags in the future
    ):
        self.logger.info("Choice selected is %s", ExamChoice(exam).name)
        await interaction.response.defer(ephemeral=True, thinking=True)
