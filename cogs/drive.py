from __future__ import print_function
import os.path, discord, sqlite3
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

        service = build('drive', 'v3', credentials=creds)

        # Call the Drive v3 API
        self.results = service.files().list(pageSize=1000, fields='files(id, name, parents, mimeType)').execute()
        self.items = self.results.get('files', [])

        # for item in enumerate(self.items):
        #     print('{:<5}{:<35}{:<95}{:<20}'.format(f'{item[0]+1}.', item[1]['mimeType'], item[1]['name'], item[1]['id']))

    @commands.group(name='drive', brief='Allows users to interact with a specific Google drive')
    async def drive(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.send('Invalid drive command passed.')
            return
        # Gets details of user from the database
        self.c.execute('SELECT Verified FROM main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        tuple = self.c.fetchone()
        if 'False' in tuple[0]:
            await ctx.send(f'Only members with a verified email can use this command, {ctx.author.mention}.')
            raise Exception('PermissionError: Absence of a verified email')

    @drive.command(name='search')
    async def search(self, ctx, *args):
        if not args:
            await ctx.send('MissingArguement: search content')
            return
        links = {}
        ignored_args = []
        for arg in args:
            if len(arg) < 3:
                ignored_args.append(arg)
                continue
            for item in self.results.get('files', []):
                if arg.lower() in item['name'].lower():
                    id = item['id']
                    name = item['name']
                    if item['parents'][0] not in links:
                        links[item['parents'][0]] = []
                    links[item['parents'][0]].append(f"[{name}](https://drive.google.com/file/d/{id})")
        if len(ignored_args) == len(args):
            embed = discord.Embed(
                description = 'The following arguements were ignored:\n"{}"'.format('" "'.join([arg for arg in ignored_args])),
                color = discord.Color.blurple()
            )
            embed.set_footer(text='Reason: Arguements must be at least 3 characters long')
            await ctx.send(embed=embed)
            return
        if not links:
            await ctx.send('Could not find anything. Sorry.')
            return
        description = ''
        for parent in links:
            for file in self.results.get('files', []):
                if file.get('id') == parent:
                    break
            description += '\n' + file.get('name') + ':\n'
            for link in links[parent]:
                description += link + '\n'
        embed = discord.Embed(
            description = description,
            color = discord.Color.blurple()
        )
        await ctx.send(embed=embed)
        if ignored_args:
            embed = discord.Embed(
                description = 'The following arguements were ignored:\n"{}"'.format('" "'.join([arg for arg in ignored_args])),
                color = discord.Color.blurple()
            )
            embed.set_footer(text='Reason: Arguements must be at least 3 characters long')
            await ctx.send(embed=embed)

    @drive.command(name='refresh')
    async def refresh(self, ctx):
        self.__init__()
        await ctx.send('Drive cache refreshed!')

def setup(bot):
    bot.add_cog(Drive(bot))
