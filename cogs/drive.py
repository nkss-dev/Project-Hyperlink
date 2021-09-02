from __future__ import print_function

import json
import os.path
from utils.l10n import get_l10n
from utils.utils import getWebhook

from discord import Embed, Color
from discord.ext import commands

from googleapiclient import errors
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

class Drive(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open('db/emojis.json') as f:
            self.emojis = json.load(f)['utility']

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
        self.l10n = get_l10n(ctx.guild.id if ctx.guild else 0, 'drive')
        return self.bot.verificationCheck(ctx)

    @commands.group(brief='Allows users to interact with a specific Google Drive')
    async def drive(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.reply(self.l10n.format_value('invalid-command', {'name': ctx.command.name}))
            return

    @drive.command(brief='Used to send search queries to the Drive')
    async def search(self, ctx, *content):
        webhook = await getWebhook(ctx.channel, self.bot.user)
        await ctx.message.add_reaction(self.emojis['loading'])

        folder_links = {}
        file_links = {}
        ignored_args = []
        for keyword in content:
            if len(keyword) < 3:
                ignored_args.append(keyword)
                continue

            page_token = None
            while True:
                try:
                    response = self.DRIVE.files().list(
                        q=f"name contains '{keyword}'",
                        spaces='drive',
                        fields='nextPageToken, files(id, name, parents, mimeType)',
                        pageToken=page_token
                    ).execute()
                except errors.HttpError:
                    await ctx.reply(self.l10n.format_value('search-error'))
                    await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)
                    return

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
                description = self.l10n.format_value('ignored-args', {'args': ', '.join([arg for arg in ignored_args])}),
                color = Color.blurple()
            )
            ignored_embed.set_footer(text=self.l10n.format_value('ignored-args-reason'))
            embeds.append(ignored_embed)

            if len(ignored_args) == len(content):
                await ctx.reply(embed=ignored_embed)
                await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)
                return

        if not folder_links and not file_links:
            await ctx.reply(self.l10n.format_value('search-result-notfound'))
            await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)
            return

        embed_title = (
            self.l10n.format_value('folders'),
            self.l10n.format_value('files')
        )

        for i, embed_name, links in zip(range(2), embed_title, (folder_links, file_links)):
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

        await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)

def setup(bot):
    bot.add_cog(Drive(bot))
