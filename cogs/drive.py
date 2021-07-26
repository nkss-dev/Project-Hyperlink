from __future__ import print_function
import os.path, discord, sqlite3, json, aiohttp
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

        # Call the Drive v3 API
        self.results = self.DRIVE.files().list(pageSize=1000, fields='files(id, name, parents, mimeType)').execute()
        self.items = self.results.get('files', [])

    @commands.group(name='drive', brief='Allows users to interact with a specific Google drive')
    async def drive(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.send('Invalid drive command passed.')
            return
        self.c.execute('SELECT Verified FROM main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        tuple = self.c.fetchone()
        if not tuple:
            raise Exception('AccountNotLinked')
        if tuple[0] == 'False':
            raise Exception('EmailNotVerified')

    @drive.command(name='search')
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
                webhook = await channel.create_webhook(name='Webhook')

        folder_links = {}
        file_links = {}
        ignored_args = []
        for keyword in content:
            if len(keyword) < 3:
                ignored_args.append(keyword)
                continue
            for item in self.items:
                if keyword.lower() in item['name'].lower():
                    id = item['id']
                    name = item['name']
                    links = file_links if item['mimeType'] != 'application/vnd.google-apps.folder' else folder_links
                    if item['parents'][0] not in links:
                        links[item['parents'][0]] = set()
                    links[item['parents'][0]].add(f"[{name}](https://drive.google.com/file/d/{id})")
                    if item['mimeType'] != 'application/vnd.google-apps.folder':
                        file_links = links
                    else:
                        folder_links = links

        embeds = []
        if ignored_args:
            ignored_embed = discord.Embed(
                description = 'The following arguements were ignored:\n{}'.format(', '.join([arg for arg in ignored_args])),
                color = discord.Color.blurple()
            )
            ignored_embed.set_footer(text='Reason: Arguments must be at least 3 characters long')
            embeds.append(ignored_embed)
            if len(ignored_args) == len(content):
                await ctx.send(embed=embed)
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
                embed = discord.Embed(
                    title = embed_name,
                    description = description,
                    color = discord.Color.blurple()
                )
                embeds.insert(i, embed)

        await webhook.send(
            embeds=embeds,
            username=self.bot.user.name,
            avatar_url=self.bot.user.avatar_url
        )

    @drive.command(name='refresh')
    async def refresh(self, ctx):
        if not await self.bot.is_owner(ctx.author):
            await ctx.reply('You need to be the owner of this bot to run this command.')
            return
        await ctx.message.add_reaction(self.emojis['loading'])
        self.__init__(self.bot)
        await ctx.send('Drive cache refreshed!')
        await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)

def setup(bot):
    bot.add_cog(Drive(bot))
