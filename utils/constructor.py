import config
import json
import os
import psycopg2
import sqlite3


class Constructor():
    """Constructs all necessary database files"""

    def __init__(self, client):
        try:
            os.mkdir('db')
        except FileExistsError:
            pass

        self.client = client
        self.funcs = (
            self.sql_databases, self.boards, self.codes, self.emojis,
            self.muted, self.VCs, self.self_roles
        )
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
    def muted():
        """Create muted.json"""
        try:
            with open('db/muted.json') as f:
                json.load(f)
        except FileNotFoundError:
            with open('db/muted.json', 'w') as f:
                json.dump([], f)

    @staticmethod
    def self_roles():
        """Create self_roles.json"""
        try:
            with open('db/self_roles.json') as f:
                json.load(f)
        except FileNotFoundError:
            with open('db/self_roles.json', 'w') as f:
                json.dump({}, f)

    def sql_databases(self):
        """Create the sql database files"""
        conn = psycopg2.connect(
            host=config.postgres.host,
            database=config.postgres.database,
            user=config.postgres.user,
            password=config.postgres.password
        )
        c = conn.cursor()

        with open('utils/records.sql') as sql:
            c.execute(sql.read())
        with open('utils/groups.sql') as sql:
            c.execute(sql.read())
        with open('utils/guilds.sql') as sql:
            c.execute(sql.read())
        conn.commit()

        self.client.db = conn
        self.client.c = c

        # links.db
        conn = sqlite3.connect('db/links.db')
        c = conn.cursor()

        with open('utils/links.sql') as sql:
            c.executescript(sql.read())
            conn.commit()

        # self_roles.db
        conn = sqlite3.connect('db/self_roles.db')
        c = conn.cursor()

        with open('utils/self_roles.sql') as sql:
            c.executescript(sql.read())
            conn.commit()

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
                'allow_text': [],
                'text_enabled_channels': [],
                'party_tchannels': {}
            }
            with open('db/VCs.json', 'w') as f:
                json.dump(VCs, f)