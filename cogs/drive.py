import json
import mimetypes
import os
import re

import discord
from discord.ext import commands

from apiclient import errors
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from utils import checks
from utils.l10n import get_l10n
from utils.utils import yesOrNo


class GoogleDrive():
    """Drive API functions"""

    def __init__(self):
        self.root = '1U2taK5kEhOiUJi70ZkU2aBWY83uVuMmD'
        self.past_papers = '13dMpIfa1FPiAdNThWdkSXfhXLK3BL-kn'

        SCOPES = ['https://www.googleapis.com/auth/drive']
        creds = None
        if os.path.exists('db/token.json'):
            creds = Credentials.from_authorized_user_file(
                'db/token.json', SCOPES
            )
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'db/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open('db/token.json', 'w') as token:
                token.write(creds.to_json())

        self.service = build('drive', 'v3', credentials=creds)

    def createFolder(self, meta_data: dict[str, str]) -> dict[str, str]:
        """Create a folder on the Drive"""
        meta_data['mimeType'] = 'application/vnd.google-apps.folder'
        payload = self.service.files().create(
            body=meta_data,
            fields='id, name, webViewLink'
        ).execute()
        return payload

    def uploadFile(self, name: str, parent_id: str = None) -> dict[str, str]:
        """Upload specified file to the given folder"""
        meta_data = {'name': name.split('/')[-1]}
        if parent_id:
            meta_data['parents'] = [parent_id]

        media = MediaFileUpload(
            name,
            mimetype=mimetypes.guess_type(name)[0],
            resumable=True
        )

        request = self.service.files().create(
            body=meta_data,
            media_body=media,
            fields='id, name, webViewLink'
        )

        response = None
        while not response:
            _, response = request.next_chunk()

        return request.execute()

    def getItem(self, id: str) -> dict[str, str]:
        """Return item details corresponding to a given ID"""
        payload = {
            'id': id,
            **self.service.files().get(fileId=id, fields='name, webViewLink').execute()
        }
        return payload

    def listItems(self, query: str) -> dict[str, str]:
        """Return all items matching the given query"""
        try:
            response = self.service.files().list(
                q=query,
                fields='nextPageToken, files(id, name, parents, mimeType, webViewLink)'
            ).execute()
        except errors.HttpError:
            return []
        files = response.get('files', [])
        nextPageToken = response.get('nextPageToken')

        while nextPageToken:
            try:
                response = self.service.files().list(
                    q=query,
                    fields='nextPageToken, files(id, name, parents, mimeType, webViewLink)',
                    pageToken=nextPageToken
                ).execute()
            except errors.HttpError:
                return []
            files.extend(response.get('files', []))
            nextPageToken = response.get('nextPageToken')

        return files

class Drive(commands.Cog):
    """Access notes and other material"""

    def __init__(self, bot):
        self.bot = bot
        self.drive = GoogleDrive()

        with open('db/emojis.json') as f:
            self.emojis = json.load(f)['utility']

    @staticmethod
    def get_query_str(args: tuple, type: str = 'default') -> tuple[str, list]:
        """Return a compatible search query for the Drive API"""
        query_args = []
        ignored_args = []
        query = ''

        if type == 'default':
            for arg in args:
                if re.match(r'(.)\1{2}', arg):
                    ignored_args.append(f'`{arg}`')
                elif len(arg) not in range (3, 21):
                    ignored_args.append(f'`{arg}`')
                else:
                    query_args.append(f"name contains '{arg}'")
            query = ' or '.join(query_args)

        return query, ignored_args

    async def cog_check(self, ctx):
        self.l10n = get_l10n(ctx.guild.id if ctx.guild else 0, 'drive')
        return checks.is_verified()

    @commands.group(invoke_without_command=True)
    async def drive(self, ctx):
        """Command group for Google Drive functionality"""
        await ctx.send_help(ctx.command)

    @drive.command()
    @commands.cooldown(2, 10.0, commands.BucketType.user)
    async def search(self, ctx, *query: tuple):
        """Search for the given query and send a corresponding embed.

        The input query is divided into separate keywords split by a space \
        character. Any keyword with less than 3 characters is ignored.

        Parameters
        ------------
        `query`: <class 'list'>
            The list of keywords to be searched on the Drive.
            Each keyword must be space separated and any multi-word keyword \
            must be enclosed inside "double quotes". Any keyword less than 2 \
            characters will be ignored.
        """
        await ctx.message.add_reaction(self.emojis['loading'])

        search_query, ignored_args = self.get_query_str(query)
        if search_query:
            files = self.drive.listItems(search_query)
        else:
            files = []

        # Sorting the links based on their parents
        file_links = {}
        folder_links = {}
        for file in files:
            parent = file['parents'][0]
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                if parent not in folder_links:
                    folder_links[parent] = []
                folder_links[parent].append(f"[{file['name']}]({file['webViewLink']})")
            else:
                if parent not in file_links:
                    file_links[parent] = []
                file_links[parent].append(f"[{file['name']}]({file['webViewLink']})")

        # Add an info embed mentioning any keywords that were ignored during the search
        embeds = []
        if ignored_args:
            ignored_embed = discord.Embed(
                description=self.l10n.format_value('ignored', {'args': ', '.join(ignored_args)}),
                color=discord.Color.blurple()
            )
            ignored_embed.set_footer(text=self.l10n.format_value('ignored-reason'))

            if len(ignored_args) == len(query):
                await ctx.reply(embed=ignored_embed)
                await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)
                return

        # Exit if no results were found for the given query
        if not files:
            await ctx.reply(self.l10n.format_value('result-notfound'))
            await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)
            return

        # Add the links to the final embed(s)
        bundle = (
            (self.l10n.format_value('folders'), self.l10n.format_value('files')),
            (folder_links, file_links)
        )
        for name, links in zip(*bundle):
            desc = ''
            for parent in links:
                parent_data = self.drive.getItem(parent)
                parent_link = f"[{parent_data['name']}]({parent_data['webViewLink']})"
                desc += f'\n**{parent_link}**:\n'
                for link in links[parent]:
                    desc += f'{link}\n'

            if desc:
                embed = discord.Embed(
                    title=name,
                    description=desc,
                    color=discord.Color.blurple()
                )
                embeds.append(embed)

        if ignored_args:
            embeds.append(ignored_embed)

        try:
            await ctx.send(embeds=embeds)
        except discord.errors.HTTPException:
            await ctx.reply(self.l10n.format_value('body-too-long'))

        await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)

    @commands.group()
    async def driveAdmin(self, ctx):
        """Command group for admin interaction with the Google Drive"""
        await commands.is_owner().predicate(ctx)
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)

    @driveAdmin.command(name='upload')
    async def uploadAttachment(self, ctx, option: str, *, file_path: str):
        """Upload message attachment to the Google Drive.

        Root folder defaults to `Notes` (ID: `1U2taK5kEhOiUJi70ZkU2aBWY83uVuMmD`)

        Parameters
        ------------
        `option`: <class 'str'>
            The procedure to be followed for uploading.
            Available options are:
                `default`: When using this option, `file_path` should be absolute. \
                    The format is as follows: `path/to/file/[file name]`. The user will \
                    be prompted each time a folder is not found in the given path. \
                    Note: To upload in the root folder, write `/[file name]`.
                `pp`: When using this option, `file_path` should be relative to the \
                    course folder. The format is as follows: `folder/[file name]`, \
                    where `folder` is the folder inside the course folder. Note \
                    that this folder will be created automatically if it does not exist.

        `file_path`: <class 'str'>
            The path of the file to upload. Format: `path/to/file/[file name]`.
            If the string ends with a `/`, i.e, if `[file name]` is not specified, \
            the file name defaults to the name of the attachment. Note that a \
            file extension needs to be specified.
        """
        if not ctx.message.attachments:
            await ctx.reply(self.l10n.format_value('attachment-notfound'))
            return

        try:
            await ctx.message.add_reaction(self.emojis['loading'])
        except discord.Forbidden:
            pass

        # Create parent folder list
        # The last folder in this list will be where the attachment is uploaded
        parents = [self.drive.getItem(self.drive.root)]
        if option == 'default':
            *file_path, filename = file_path.split('/')

            # Loop through each folder and append them to the parent folder list
            for folder in file_path:
                query = f"""name = '{folder}' and
                    mimeType = 'application/vnd.google-apps.folder' and
                    parents = '{parents[-1]['id']}'"""
                folder_details = self.drive.listItems(query)

                # Ask the user if they wish to create a new folder
                if not folder_details:
                    message = await ctx.reply(
                        self.l10n.format_value('folder-notfound', {'folder': folder})
                    )
                    if await yesOrNo(ctx, message):
                        meta_data = {'name': folder, 'parents': [parents[-1]['id']]}
                        parents.append(self.drive.createFolder(meta_data))
                    else:
                        await ctx.send('upload-cancelled')
                        await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)
                        return
                else:
                    parents.append(folder_details[0])

            # Default to the attachment name if file name is not specified
            if not filename:
                filename = ctx.message.attachments[0].filename.replace('_', ' ')

        elif option == 'pp':
            folder, filename = file_path.split('/', 1)

            # Default to the attachment name if file name is not specified
            if not filename:
                filename = ctx.message.attachments[0].filename.replace('_', ' ')

            # Get main course folder
            parents.append(self.drive.getItem(self.drive.past_papers))
            query = f"""name contains '{filename.split(' ', 1)[0]}' and
                mimeType = 'application/vnd.google-apps.folder' and
                parents = '{parents[-1]['id']}'"""
            course_folder = self.drive.listItems(query)

            if not course_folder:
                question = await ctx.reply(self.l10n.format_value('enter-folder-name'))

                def check(message: discord.Message) -> bool:
                    """Check if the message sent is by the command author in the right channel"""
                    return message.author == ctx.author and message.channel == ctx.channel

                # Wait for the user to give a name for the course folder
                message = await self.bot.wait_for('message', check=check)
                if message.content.lower() == 'cancel':
                    await ctx.send('upload-cancelled')
                    await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)
                    return
                await question.delete()
                if ctx.guild and ctx.guild.me.guild_permissions.manage_messages:
                    await message.delete()

                # Create the course folder and the subsequent child folder
                meta_data = {'name': message.content, 'parents': [parents[-1]['id']]}
                parents.append(self.drive.createFolder(meta_data))
                meta_data = {
                    'name': folder,
                    'parents': [parents[-1]['id']]
                }
                parents.append(self.drive.createFolder(meta_data))

            else:
                parents.append(course_folder[0])
                query = f"""name = '{folder}' and
                    mimeType = 'application/vnd.google-apps.folder' and
                    parents = '{course_folder[0]['id']}'"""
                parent = self.drive.listItems(query)

                # Create the child folder
                if not parent:
                    meta_data = {'name': folder, 'parents': [course_folder[0]['id']]}
                    parents.append(self.drive.createFolder(meta_data))
                else:
                    parents.append(parent[0])
        else:
            vars = {
                'option': option,
                'prefix': ctx.clean_prefix,
                'command': ctx.command.qualified_name
            }
            await ctx.reply(self.l10n.format_value('invalid-option', vars))
            await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)
            return

        # Download the attachment
        try:
            os.mkdir('temp')
        except FileExistsError:
            pass
        await ctx.message.attachments[0].save(f'temp/{filename}')

        # Upload the attachment
        file = self.drive.uploadFile(f'temp/{filename}', parents[-1]['id'])

        # Create directory tree string
        tree = ''
        for i, parent in enumerate(parents):
            tree += f"[{parent['name']}]({parent['webViewLink']})\n{'​ '*i*6}╰> "
        tree += f"[{file['name']}]({file['webViewLink']})"

        embed = discord.Embed(
            title=self.l10n.format_value('upload-successful'),
            description=tree,
            color=discord.Color.blurple()
        )
        await ctx.reply(embed=embed)
        await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)

        # Cleanup
        os.remove(f'temp/{filename}')


def setup(bot):
    """Called when this file is attempted to be loaded as an extension"""
    bot.add_cog(Drive(bot))
