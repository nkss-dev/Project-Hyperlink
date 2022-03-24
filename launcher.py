# Run this script for first time setups

import json
import os
import sqlite3

try:
    os.mkdir('db')
except FileExistsError:
    pass

# jsons
jsons = {
    'boards': {},
    'codes': {},
    'emojis': {
        'utility': {
            'loading': '',
            'no': '',
            'not-verified': '',
            'triggered': '',
            'verified': '',
            'yes': ''
        },
        'games': {}
    },
    'muted': [],
    'self_roles': {},
    'VCs': {
        'vc_enabled_channels': [],
        'party_vchannels': [],
        'allow_text': [],
        'text_enabled_channels': [],
        'party_tchannels': {}
    },
}

for json_name, content in jsons.items():
    try:
        with open(f'db/{json_name}.json', 'r') as file:
            json.load(file)
    except FileNotFoundError:
        with open(f'db/{json_name}.json', 'w') as file:
            json.dump(content, file)

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
