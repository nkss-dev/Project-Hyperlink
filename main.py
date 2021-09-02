import json

from discord import Intents
from discord.ext.commands import Bot

import os
from dotenv import load_dotenv
load_dotenv()

def get_prefix(_, message):
    if message.guild:
        with open('db/guilds.json') as f:
            prefixes = json.load(f)
        return  prefixes[str(message.guild.id)]['prefix']
    return '%'

client = Bot(
    command_prefix=get_prefix,
    intents=Intents.all(),
    owner_ids=list(map(int, os.environ['OWNER_IDS'].split(', ')))
)

@client.event
async def on_ready():
    print(f'Logged on as {client.user}!')

    client.default_guild_details = {
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
            'kick': [0, '{user} has been kicked from the server.'],
            'ban': [0, '{user} has been banned from the server.'],
            'welcome': ''
        },
        'log': [0, 0]
    }

    try:
        with open('db/guilds.json') as f:
            client.guild_data = json.load(f)
        for guild in client.guild_data:
            for key in client.default_guild_details:
                if key not in client.guild_data[guild]:
                    client.guild_data[guild][key] = client.default_guild_details[key]
        with open('db/guilds.json', 'w') as f:
            json.dump(client.guild_data, f)
    except FileNotFoundError:
        # Creates the guilds.json file if it doesn't exist, as it is essential for many cogs' functioning
        client.guild_data = {guild.id: client.default_guild_details for guild in client.guilds}
        with open('db/guilds.json', 'w') as f:
            json.dump(client.guild_data, f)

    # Loads all the cogs
    errors = []
    for i, filename in enumerate(os.listdir('./cogs'), start=1):
        if filename.endswith('.py'):
            try:
                client.load_extension(f'cogs.{filename[:-3]}')
            except Exception as error:
                errors.append(error)
    i -= 1
    print(f'{i-len(errors)}/{i} cogs loaded successfully!')
    for error in errors:
        print(error)

client.run(os.environ['BOT_TOKEN'])
