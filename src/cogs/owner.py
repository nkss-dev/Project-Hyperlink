import os
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands

from base.cog import HyperlinkCog
from cogs import ALL_EXTENSIONS
import cogs.checks as checks
from main import ProjectHyperlink
from utils.utils import is_alone, yesOrNo


class OwnerOnly(HyperlinkCog):
    """Bot owner commands"""

    async def interaction_check(
        self, interaction: discord.Interaction[ProjectHyperlink]
    ) -> bool:
        checks._is_dev_guild(interaction)
        await checks._is_owner(interaction)

        l10n = await self.bot.get_l10n(interaction.guild_id or 0)
        self.fmv = l10n.format_value

        return super().interaction_check(interaction)

    def cog_check(self, ctx: commands.Context[ProjectHyperlink]) -> bool:
        return checks._is_dev_guild(ctx)

    async def load_autocomplete(self, _: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=extension[5:], value=extension)
            for extension in ALL_EXTENSIONS
            if extension not in self.bot.extensions
            and current.lower() in extension.lower()
        ]

    async def unload_autocomplete(self, _: discord.Interaction, current: str):
        return [
            app_commands.Choice(name=extension[5:], value=extension)
            for extension in self.bot.extensions
            if current.lower() in extension.lower()
        ]

    @app_commands.command()
    @app_commands.autocomplete(extension=load_autocomplete)
    async def load(self, interaction: discord.Interaction, extension: str):
        """Load an extension.

        Loads extension present in the `/cogs` directory

        Paramters
        -----------
        `extension`: <class 'str'>
            The extension to load. Does not need to contain `.py` at the end.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)
        await self.bot.load_extension(f"{extension}")
        await interaction.followup.send(
            self.fmv("load-successful", {"ext": extension}), ephemeral=True
        )

    @app_commands.command()
    @app_commands.autocomplete(extension=unload_autocomplete)
    async def unload(self, interaction: discord.Interaction, extension: str):
        """Unload an extension.

        Paramters
        -----------
        extension: <class 'str'>
            The extension to unload.
        """
        await self.bot.unload_extension(f"{extension}")
        await interaction.response.send_message(
            self.fmv("unload-successful", {"ext": extension}), ephemeral=True
        )

    @app_commands.command()
    @app_commands.autocomplete(extension=unload_autocomplete)
    async def reload(self, interaction: discord.Interaction, extension: str):
        """Reload an extension.

        Paramters
        -----------
        extension: <class 'str'>
            The extension to reload.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)
        await self.bot.reload_extension(f"{extension}")
        await interaction.followup.send(
            self.fmv("reload-successful", {"ext": extension}), ephemeral=True
        )

    @commands.command()
    @commands.guild_only()
    async def sync(
        self,
        ctx: commands.Context,
        guilds: commands.Greedy[discord.Object],
        spec: Optional[Literal["~", "*", "^"]] = None,
    ) -> None:
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


async def setup(bot):
    await bot.add_cog(OwnerOnly(bot))
