from enum import Enum
from typing import Any

import discord
from discord.app_commands import Choice, Group

from base.cog import HyperlinkGroupCog
from cogs.drive.ui import DriveSearchView
from main import ProjectHyperlink


class Exam(Enum):
    MID_SEM_1 = "Mid Sem - 1"
    MID_SEM_2 = "Mid Sem - 2"
    MID_SEM_3 = "Mid Sem - 3"
    END_SEM = "End Sem"

    def __init__(self, *args, **kwargs) -> None:
        self._name_ = self._value_


class Drive(
    HyperlinkGroupCog,
    group_name="drive",
    group_description="All the commands related to NKSS-Drive",
):
    def __init__(self, bot: ProjectHyperlink, *args: Any, **kwargs: Any) -> None:
        super().__init__(bot, *args, **kwargs)
        # TODO - call the api to load courses
        self.courses_dict = {
            "ecpc33": "Random Variables",
            "cspc20": "Operating Systems",
            "itpc20": "Operating Systems",
        }

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

    async def course_name_autocomplete(
        self, interaction: discord.Interaction[ProjectHyperlink], current: str
    ) -> list[Choice[str]]:
        return [
            Choice(name=course_name + " - " + course_code.upper(), value=course_code)
            for course_code, course_name in self.courses_dict.items()
            if current.lower() in course_name.lower()
        ]

    @discord.app_commands.command(description="Upload a past paper.")
    @discord.app_commands.autocomplete(course_name=course_name_autocomplete)
    async def past_paper(
        self,
        interaction: discord.Interaction[ProjectHyperlink],
        exam: Exam,
        course_name: str,
        file: discord.Attachment,
        # TODO: add tags in the future
    ):
        # self.logger.info("Choice selected is %s", exam)
        await interaction.response.send_message(
            content=f"Your exam is : {exam.name} and course is: {self.courses_dict[course_name]}, code is: {course_name}"
        )
        # await interaction.response.defer(thinking=True)
