import json
import os
import sqlite3

class Constructor():
    def __init__(self, client):
        print(f'Logged on as {client.user}')

        try:
            os.mkdir('db')
        except FileExistsError:
            pass

        self.client = client
        self.funcs = [
            self.boards,
            self.codes,
            self.details,
            self.emojis,
            self.games,
            self.guilds,
            self.links,
            self.muted,
            self.reactionRoles,
            self.VCs,
            self.loadCogs
        ]

    # boards.json
    @staticmethod
    def boards():
        try:
            with open('db/boards.json') as f:
                json.load(f)
        except FileNotFoundError:
            with open('db/boards.json', 'w') as f:
                json.dump({}, f)

    # codes.json
    @staticmethod
    def codes():
        try:
            with open('db/codes.json') as f:
                json.load(f)
        except FileNotFoundError:
            with open('db/codes.json', 'w') as f:
                json.dump({}, f)

    # details.db
    @staticmethod
    def details():
        conn = sqlite3.connect('db/details.db')
        c = conn.cursor()

        try:
            c.execute('''
                CREATE TABLE main (
                    Roll_Number integer PRIMARY KEY,
                    Section text,
                    SubSection text,
                    Name text,
                    Gender text,
                    Institute_Email text,
                    Batch integer,
                    Discord_UID integer UNIQUE,
                    Guilds text DEFAULT "[]",
                    Verified text DEFAULT "False",
                    IGN text DEFAULT '{}'
                )
            ''')
            c.execute('''
                CREATE TABLE voltorb (
                    Discord_UID integer,
                    level text,
                    coins text,
                    total text,
                    lose text,
                    win text,
                    rip text,
                    message text,
                    row text,
                    col text,
                    board text,
                    flip text,
                    bg blob,
                    voltorb_tile blob,
                    tile_1 blob,
                    tile_2 blob,
                    tile_3 blob,
                    hl_voltorb_tile blob,
                    FOREIGN KEY(Discord_UID) REFERENCES main(Discord_UID)
                )
            ''')
            conn.commit()
        except sqlite3.OperationalError:
            pass

    # emojis.json
    @staticmethod
    def emojis():
        try:
            with open('db/emojis.json') as f:
                json.load(f)
        except FileNotFoundError:
            emojis = {
            	'utility': {
            		'verified': '',
            		'not-verified': '',
            		'triggered': '',
            		'loading': ''
            	},
            	'games': {}
            }
            with open('db/emojis.json', 'w') as f:
                json.dump(emojis, f)

    # games.json
    @staticmethod
    def games():
        try:
            with open('db/games.json') as f:
                json.load(f)
        except FileNotFoundError:
            with open('db/games.json', 'w') as f:
                json.dump([], f)

    # guilds.json
    def guilds(self):
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
                guild.id: self.client.default_guild_details for guild in self.client.guilds
            }
            with open('db/guilds.json', 'w') as f:
                json.dump(self.client.guild_data, f)

    # links.json
    @staticmethod
    def links():
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

    # muted.json
    @staticmethod
    def muted():
        try:
            with open('db/muted.json') as f:
                json.load(f)
        except FileNotFoundError:
            with open('db/muted.json', 'w') as f:
                json.dump([], f)

    # reactionRoles.json
    @staticmethod
    def reactionRoles():
        try:
            with open('db/reactionRoles.json') as f:
                json.load(f)
        except FileNotFoundError:
            with open('db/reactionRoles.json', 'w') as f:
                json.dump({}, f)

    # VCs.json
    @staticmethod
    def VCs():
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
