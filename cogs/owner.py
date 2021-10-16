import json
import os

import discord
from discord.ext import commands

from utils.l10n import get_l10n
from utils.utils import yesOrNo


class OwnerOnly(commands.Cog):
    """Bot owner commands"""

    def __init__(self, bot):
        self.bot = bot

        with open('db/emojis.json') as f:
            self.emojis = json.load(f)['utility']

    async def cog_check(self, ctx) -> bool:
        self.l10n = get_l10n(ctx.guild.id if ctx.guild else 0, 'owner')
        return await commands.is_owner().predicate(ctx)

    @commands.command()
    async def load(self, ctx, extension: str):
        """Load an extension.

        Loads extension present in the `/cogs` directory

        Paramters
        -----------
        `extension`: <class 'str'>
            The extension to load. Does not need to contain `.py` at the end.
        """
        await ctx.message.add_reaction(self.emojis['loading'])

        self.bot.load_extension(f'cogs.{extension}')

        await ctx.send(self.l10n.format_value('load-successful', {'ext': extension}))

        await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)

    @commands.command()
    async def unload(self, ctx, extension: str):
        """Unload an extension.

        Paramters
        -----------
        extension: <class 'str'>
            The extension to unload.
        """
        await ctx.message.add_reaction(self.emojis['loading'])

        self.bot.unload_extension(f'cogs.{extension}')

        await ctx.send(self.l10n.format_value('unload-successful', {'ext': extension}))

        await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)

    @commands.command()
    async def reload(self, ctx, extension: str):
        """Reload an extension.

        Paramters
        -----------
        extension: <class 'str'>
            The extension to reload.
        """
        await ctx.message.add_reaction(self.emojis['loading'])

        self.bot.unload_extension(f'cogs.{extension}')
        self.bot.load_extension(f'cogs.{extension}')

        await ctx.send(self.l10n.format_value('reload-successful', {'ext': extension}))

        await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)

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
        if isinstance(ctx.channel, (discord.TextChannel, discord.Thread)):
            members_exist = False
            if isinstance(ctx.channel, discord.Thread):
                for member in await ctx.channel.fetch_members():
                    if not ctx.guild.get_member(member.id).bot and member.id != ctx.author.id:
                        members_exist = True
                        break
            else:
                for member in ctx.channel.members:
                    if not member.bot:
                        members_exist = True
                        break

            if members_exist:
                message = await ctx.reply(self.l10n.format_value('reveal-check'))
                if not await yesOrNo(ctx, message):
                    await ctx.send(self.l10n.format_value('archive-cancel'))
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
            await ctx.send(self.l10n.format_value('file-notfound'))
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
            await ctx.reply(self.l10n.format_value('attachment-notfound'))
            return

        if filenames:
            filenames = filenames.split(',')
        else:
            filenames = []
        if diff := len(ctx.message.attachments) - len(filenames) > 0:
            filenames.extend([None]*diff)
        for filename, attachment in zip(filenames, ctx.message.attachments):
            await attachment.save(f'db/{filename or attachment.filename}')

        await ctx.send(self.l10n.format_value('upload-success'))

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

        await ctx.send(self.l10n.format_value('remove-success'))


def setup(bot):
    """Called when this file is attempted to be loaded as an extension"""
    bot.add_cog(OwnerOnly(bot))
