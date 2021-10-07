import json
import os
import sqlite3

class Constructor():
    def __init__(self, client):
        print(f'Logged in as {client.user} (ID: {client.user.id})')

        try:
            os.mkdir('db')
        except FileExistsError:
            pass

        self.client = client
        self.funcs = [
            self.boards,
            self.codes,
            self.emojis,
            self.games,
            self.guilds,
            self.links,
            self.muted,
            self.reactionRoles,
            self.VCs,
            self.sql_databases,
            self.loadCogs
        ]
        for func in self.funcs:
            func()

    @staticmethod
    def boards():
        """Create boards.json"""
        try:
            with open('db/boards.json') as f:
                json.load(f)
        except FileNotFoundError:
            with open('db/boards.json', 'w') as f:
                json.dump({}, f)

    @staticmethod
    def codes():
        """Create codes.json"""
        try:
            with open('db/codes.json') as f:
                json.load(f)
        except FileNotFoundError:
            with open('db/codes.json', 'w') as f:
                json.dump({}, f)

    @staticmethod
    def emojis():
        """Create emojis.json"""
        try:
            with open('db/emojis.json') as f:
                json.load(f)
        except FileNotFoundError:
            emojis = {
                'utility': {
                    'loading': '',
                    'no': '',
                    'not-verified': '',
                    'triggered': '',
                    'verified': '',
                    'yes': ''
                },
                'games': {}
            }
            with open('db/emojis.json', 'w') as f:
                json.dump(emojis, f)

    @staticmethod
    def games():
        """Create games.json"""
        try:
            with open('db/games.json') as f:
                json.load(f)
        except FileNotFoundError:
            with open('db/games.json', 'w') as f:
                json.dump([], f)

    def guilds(self):
        """Create guilds.json"""
        self.client.default_guild_details = {
            'prefix': ['%'],
            'roles': {
                'bot': 0,
                'join': [],
                'mod': [],
                'mute': 0
            },
            'events': {
                'join': [0, '{user} has joined the server!'],
                'leave': [0, '{user} has left the server.'],
                'kick': [0, '{user} has been kicked from the server by {member}.'],
                'ban': [0, '{user} has been banned from the server by {member}.'],
                'welcome': ''
            },
            'log': [0, 0]
        }

        try:
            with open('db/guilds.json') as f:
                self.client.guild_data = json.load(f)

            for guild in self.client.guild_data:
                for key in self.client.default_guild_details:
                    if key not in self.client.guild_data[guild]:
                        self.client.guild_data[guild][key] = self.client.default_guild_details[key]

            with open('db/guilds.json', 'w') as f:
                json.dump(self.client.guild_data, f)
        except FileNotFoundError:
            self.client.guild_data = {
                str(guild.id): self.client.default_guild_details for guild in self.client.guilds
            }
            with open('db/guilds.json', 'w') as f:
                json.dump(self.client.guild_data, f)

    @staticmethod
    def links():
        """Create links.json"""
        try:
            with open('db/links.json') as f:
                json.load(f)
        except FileNotFoundError:
            sections = (
                'CE-A', 'CE-B', 'CE-C',
                'CS-A', 'CS-B',
                'EC-A', 'EC-B', 'EC-C',
                'EE-A', 'EE-B', 'EE-C',
                'IT-A', 'IT-B',
                'ME-A', 'ME-B', 'ME-C',
                'PI-A', 'PI-B'
            )

            conn = sqlite3.connect('db/details.db')
            c = conn.cursor()
            batches = c.execute('select distinct Batch from main').fetchall()
            batches = [batch[0] for batch in batches]

            links = {
                batch: {
                    'server_ID': [],
                    'manager_roles': [],
                    **{section: {
                        'channel': 0,
                        'message': 0,
                        'Monday': [],
                        'Tuesday': [],
                        'Wednesday': [],
                        'Thursday': [],
                        'Friday': [],
                        'Saturday': [],
                        'Sunday': []
                    } for section in sections}
                } for batch in batches
            }
            with open('db/links.json', 'w') as f:
                json.dump(links, f)

    @staticmethod
    def muted():
        """Create muted.json"""
        try:
            with open('db/muted.json') as f:
                json.load(f)
        except FileNotFoundError:
            with open('db/muted.json', 'w') as f:
                json.dump([], f)

    @staticmethod
    def reactionRoles():
        """Create reactionRoles.json"""
        try:
            with open('db/reactionRoles.json') as f:
                json.load(f)
        except FileNotFoundError:
            with open('db/reactionRoles.json', 'w') as f:
                json.dump({}, f)
    def sql_databases(self):
        """Create details.db and self_roles.db"""
        # details.db
        conn = sqlite3.connect('db/details.db')
        c = conn.cursor()

        with open('utils/details.sql') as sql:
            c.executescript(sql.read())
            conn.commit()

        self.client.db = conn
        self.client.c = c

    @staticmethod
    def VCs():
        """Create VCs.json"""
        try:
            with open('db/VCs.json') as f:
                json.load(f)
        except FileNotFoundError:
            VCs = {
                'vc_enabled_channels': [],
                'party_vchannels': [],
                'allow_text': {},
                'text_enabled_channels': [],
                'party_tchannels': {}
            }
            with open('db/VCs.json', 'w') as f:
                json.dump(VCs, f)

    def loadCogs(self):
        """load all the .py files in the `cogs` folder as extension"""
        errors = []
        for i, filename in enumerate(os.listdir('./cogs'), start=1):
            if filename.endswith('.py'):
                try:
                    self.client.load_extension(f'cogs.{filename[:-3]}')
                except Exception as error:
                    errors.append(error)
        i -= 1
        print(f'{i-len(errors)}/{i} cogs loaded successfully!\n')
        for error in errors:
            print(error)
