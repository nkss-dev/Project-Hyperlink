from __future__ import print_function

import aiohttp
import json
import os.path
import sqlite3

from discord import Embed, Color
from discord.ext import commands

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

class Drive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

        with open('db/emojis.json', 'r') as f:
            self.emojis = json.load(f)

        SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
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

        self.DRIVE = build('drive', 'v3', credentials=creds)

    async def cog_check(self, ctx):
        return self.bot.verificationCheck(ctx)

    @commands.group(brief='Allows users to interact with a specific Google Drive')
    async def drive(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.send('Invalid drive command passed.')
            return

    @drive.command(brief='Used to send search queries to the Drive')
    async def search(self, ctx, *content):
        bool = False
        async with aiohttp.ClientSession() as session:
            # Checks if a webhook already exists for that channel
            webhooks = await ctx.channel.webhooks()
            for webhook in webhooks:
                if webhook.user == self.bot.user:
                    bool = True
                    break
            # Creates a webhook if none exist
            if not bool:
                webhook = await ctx.channel.create_webhook(name='Webhook')

        folder_links = {}
        file_links = {}
        ignored_args = []
        for keyword in content:
            if len(keyword) < 3:
                ignored_args.append(keyword)
                continue

            page_token = None
            while True:
                response = self.DRIVE.files().list(
                    q=f"name contains '{keyword}'",
                    spaces='drive',
                    fields='nextPageToken, files(id, name, parents, mimeType)',
                    pageToken=page_token
                ).execute()
                for file in response.get('files', []):
                    links = file_links if file.get('mimeType') != 'application/vnd.google-apps.folder' else folder_links
                    if file.get('parents')[0] not in links:
                        links[file.get('parents')[0]] = set()
                    links[file.get('parents')[0]].add(f"[{file.get('name')}](https://drive.google.com/file/d/{file.get('id')})")
                    if file.get('mimeType') != 'application/vnd.google-apps.folder':
                        file_links = links
                    else:
                        folder_links = links
                page_token = response.get('nextPageToken', None)
                if page_token is None:
                    break

        embeds = []
        if ignored_args:
            ignored_embed = Embed(
                description = 'The following arguements were ignored:\n{}'.format(', '.join([arg for arg in ignored_args])),
                color = Color.blurple()
            )
            ignored_embed.set_footer(text='Reason: Arguments must be at least 3 characters long')
            embeds.append(ignored_embed)
            if len(ignored_args) == len(content):
                await ctx.send(embed=ignored_embed)
                return

        if not folder_links and not file_links:
            await ctx.send('Could not find anything. Sorry.')
            return

        for i, embed_name, links in zip(range(2), ['Folders', 'Files'], [folder_links, file_links]):
            description = ''
            for parent in links:
                data = self.DRIVE.files().get(fileId=parent).execute()
                description += f"\n{data['name']}:\n"
                for link in links[parent]:
                    description += f'{link}\n'

            if description:
                embed = Embed(
                    title = embed_name,
                    description = description,
                    color = Color.blurple()
                )
                embeds.insert(i, embed)

        await webhook.send(
            embeds=embeds,
            username=self.bot.user.name,
            avatar_url=self.bot.user.avatar_url
        )

def setup(bot):
    bot.add_cog(Drive(bot))
