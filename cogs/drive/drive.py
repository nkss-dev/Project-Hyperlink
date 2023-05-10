import discord
from discord.app_commands import Choice, Group

from base.cog import HyperlinkGroupCog
from cogs.drive.ui import DriveSearchView, DriveSearchResultEmbed
from main import ProjectHyperlink


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

        contents = ["foo", "bar", "baz", "spam", "egg"]
        embed = DriveSearchResultEmbed("Results", description=contents[0])
        view = DriveSearchView(
            interaction.user,
            contents,
            embed,
        )
        await interaction.response.send_message(embed=embed, view=view)
        # await view.wait()
        # await interaction.edit_original_response(view=None)

    upload = Group(
        name="upload", description="Upload message attachment to the Google Drive."
    )

    @discord.app_commands.command(description="Upload a past paper.")
    @discord.app_commands.choices(
        exam=[  # TODO: probably use an enum for the choices
            Choice(name="Mid Sem - 1", value="ms1"),
            Choice(name="Mid Sem - 2", value="ms2"),
            Choice(name="Mid Sem - 3", value="ms3"),
            Choice(name="End Sem", value="es"),
        ]
    )
    async def past_paper(
        self,
        interaction: discord.Interaction[ProjectHyperlink],
        exam: Choice[str],
        file: discord.Attachment,
        # TODO: add tags in the future
    ):
        await interaction.response.defer(ephemeral=True, thinking=True)
