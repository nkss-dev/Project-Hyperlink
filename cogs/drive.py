import json
import mimetypes
from typing import Dict, Tuple

from utils.l10n import get_l10n
from utils.utils import getWebhook

import discord
from discord.ext import commands

import os.path
from apiclient import errors
from apiclient.discovery import build
from apiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

class GoogleDrive():
    def __init__(self):
        SCOPES = ['https://www.googleapis.com/auth/drive']
        creds = None
        if os.path.exists('db/token.json'):
            creds = Credentials.from_authorized_user_file('db/token.json', SCOPES)
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

    def createFolder(self, meta_data):
        """creates a folder on the Drive"""
        meta_data['mimeType'] = 'application/vnd.google-apps.folder'
        self.service.files().create(body=meta_data).execute()

    def uploadFile(self, name, parent_id=None) -> str:
        """uploads specified file to the given folder"""
        meta_data = {'name': name}
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
            fields='id'
        )

        response = None
        while not response:
            _, response = request.next_chunk()

        return request.execute().get('id')

    def getItem(self, id) -> Tuple[str, str]:
        """returns item details corresponding to a given ID"""
        return self.service.files().get(fileId=id, fields='name, webViewLink').execute()

    def listItems(self, query) -> Dict[str, str]:
        """lists all items matching the given query"""
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
    def __init__(self, bot):
        self.bot = bot
        self.drive = GoogleDrive()

        with open('db/emojis.json') as f:
            self.emojis = json.load(f)['utility']

    @staticmethod
    def getSearchQuery(query, type: str='default') -> Tuple[str, str]:
        """returns a compatible search query for the Drive API"""
        search_query = []
        ignored_args = []

        if type == 'default':
            for keyword in query:
                if len(keyword) < 3:
                    ignored_args.append(keyword)
                else:
                    search_query.append(f"name contains '{keyword}'")
            search_query = ' or '.join(search_query)

        return search_query, ignored_args

    async def cog_check(self, ctx) -> bool:
        self.l10n = get_l10n(ctx.guild.id if ctx.guild else 0, 'drive')
        return self.bot.verificationCheck(ctx)

    @commands.group()
    async def drive(self, ctx):
        """Main command for interacting with the Google Drive"""
        if not ctx.invoked_subcommand:
            await ctx.reply(self.l10n.format_value('invalid-command', {'name': ctx.command.name}))
            return

    @drive.command()
    async def search(self, ctx, *query):
        """Searches for the query and sends a corresponding embed"""
        await ctx.message.add_reaction(self.emojis['loading'])

        search_query, ignored_args = self.getSearchQuery(query)
        files = self.drive.listItems(search_query)

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
                await ctx.message.remove_reaction(self.emojis['loading'], ctx.guild.me)
                return

        # Exit if no results were found for the given query
        if not files:
            await ctx.reply(self.l10n.format_value('result-notfound'))
            await ctx.message.remove_reaction(self.emojis['loading'], ctx.guild.me)
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
                embed = discord.Embed(title=name, description=desc, color=discord.Color.blurple())
                embeds.append(embed)

        if ignored_args:
            embeds.append(ignored_embed)

        if len(embeds) > 1 and ctx.guild and (webhook := await getWebhook(ctx.channel, ctx.guild.me)):
            try:
                await webhook.send(
                    embeds=embeds,
                    username=ctx.guild.me.nick or ctx.guild.me.name,
                    avatar_url=ctx.guild.me.avatar.url
                )
            except discord.errors.HTTPException:
                await ctx.reply(self.l10n.format_value('body-too-long'))
        else:
            for embed in embeds:
                await ctx.send(embed=embed)

        await ctx.message.remove_reaction(self.emojis['loading'], ctx.guild.me)

def setup(bot):
    bot.add_cog(Drive(bot))
