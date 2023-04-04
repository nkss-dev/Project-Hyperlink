import os
from typing import Literal, Optional

import discord
from discord import app_commands
from discord.ext import commands

from base.cog import HyperlinkCog
import cogs.checks as checks
from main import ProjectHyperlink
from utils.utils import is_alone, yesOrNo


# TODO: Make these dev guild only
class OwnerOnly(HyperlinkCog):
    """Bot owner commands"""

    async def interaction_check(
        self, interaction: discord.Interaction[ProjectHyperlink]
    ) -> bool:
        await checks._is_owner(interaction)

        l10n = await self.bot.get_l10n(interaction.guild_id or 0)
        self.fmv = l10n.format_value

        return super().interaction_check(interaction)

    @app_commands.command()
    async def load(self, interaction: discord.Interaction, extension: str):
        """Load an extension.

        Loads extension present in the `/cogs` directory

        Paramters
        -----------
        `extension`: <class 'str'>
            The extension to load. Does not need to contain `.py` at the end.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)
        await self.bot.load_extension(f"cogs.{extension}")
        await interaction.followup.send(
            self.fmv("load-successful", {"ext": extension}), ephemeral=True
        )

    @app_commands.command()
    async def unload(self, interaction: discord.Interaction, extension: str):
        """Unload an extension.

        Paramters
        -----------
        extension: <class 'str'>
            The extension to unload.
        """
        await self.bot.unload_extension(f"cogs.{extension}")
        await interaction.response.send_message(
            self.fmv("unload-successful", {"ext": extension}), ephemeral=True
        )

    @app_commands.command()
    async def reload(self, interaction: discord.Interaction, extension: str):
        """Reload an extension.

        Paramters
        -----------
        extension: <class 'str'>
            The extension to reload.
        """
        await interaction.response.defer(ephemeral=True, thinking=True)
        await self.bot.reload_extension(f"cogs.{extension}")
        await interaction.followup.send(
            self.fmv("reload-successful", {"ext": extension}), ephemeral=True
        )



    @commands.group(aliases=['db'], invoke_without_command=True)
    async def database(self, ctx):
        """Command group for database read/write commands"""
        await ctx.send_help(ctx.command)

    @database.command(aliases=['arc', 'arch'])
    async def archive(self, ctx, *filenames):
        """Create a save state of the database files.

        Paramters
        -----------
        `filenames`: Optional[list[str]]
            A list of file names of the files to archive. If not specified, \
            all files in the database folder will be archived.
        """
        if not await is_alone(ctx.channel, ctx.author, self.bot.user):
            message = await ctx.reply(self.fmv('reveal-check'))
            if not await yesOrNo(ctx, message):
                await ctx.send(self.fmv('archive-cancel'))
                return

        files = []
        if filenames:
            for filename in filenames:
                try:
                    files.append(discord.File(f'db/{filename}'))
                except FileNotFoundError:
                    pass
        else:
            for i, filename in enumerate(os.listdir('./db'), start=1):
                files.append(discord.File(f'db/{filename}'))

        # Dividing the files into lists of 10 as the
        # max. limit of attachments per message is 10
        files = [files[i:i+10] for i in range(0, len(files), 10)]

        if not files:
            await ctx.send(self.fmv('file-notfound'))
        for ten_files in files:
            await ctx.send(files=ten_files)

    @database.command()
    async def add(self, ctx, *, filenames):
        """Add file(s) to the database folder.

        Paramters
        -----------
        `filenames`: <class 'str'>
            A comma-separated string of the file names of the files to add.
            If there are more file names than files, the remaining file names \
            will be discarded. If left blank, the file names will default to \
            the attachment names. To leave certain file names blank, enter two \
            or more consecutive commas; hence, leaving those files' name blank.
        """
        if not ctx.message.attachments:
            await ctx.reply(self.fmv('attachment-notfound'))
            return

        if filenames:
            filenames = filenames.split(',')
        else:
            filenames = []
        if diff := len(ctx.message.attachments) - len(filenames) > 0:
            filenames.extend([None]*diff)
        for filename, attachment in zip(filenames, ctx.message.attachments):
            await attachment.save(f'db/{filename or attachment.filename}')

        await ctx.send(self.fmv('upload-success'))

    @database.command(aliases=['rm'])
    async def remove(self, ctx, *filenames):
        """Remove file(s) from the database folder.

        Paramters
        -----------
        `filenames`: <class 'list'>
            The list of file names to remove.
        """
        for filename in filenames:
            os.remove(f'db/{filename}')

        await ctx.send(self.fmv('remove-success'))

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
