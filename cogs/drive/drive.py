from enum import Enum

import config
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
    async def cog_load(self) -> None:
        async with self.bot.session.get(f"{config.api_url}/courses") as resp:
            if resp.status == 200:
                courses = (await resp.json())["data"]
                self.courses = {course["code"]: course["title"] for course in courses}
            else:
                self.logger.exception("Courses data could not be loaded")

        return await super().cog_load()

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
        name="upload", description="Upload message attachment to the NKSSS Drive."
    )

    async def course_name_autocomplete(
        self, interaction: discord.Interaction[ProjectHyperlink], current: str
    ) -> list[Choice[str]]:
        return [
            Choice(name=course_code, value=course_code)
            for course_code, course_name in self.courses.items()
            if current.lower() in course_name.lower()
            or current.lower() in course_code.lower()
        ]

    @upload.command(description="Upload a past paper.")
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
            content=f"Your exam is : {exam.name} and course is: {self.courses[course_name]}, code is: {course_name}"
        )
        # await interaction.response.defer(thinking=True)
