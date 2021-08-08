import os, json
from discord import Intents
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

def get_prefix(client, message):
    with open('db/guilds.json', 'r') as f:
        prefixes = json.load(f)
    return prefixes[str(message.guild.id)]['prefix']

client = commands.Bot(command_prefix=get_prefix, intents=Intents.all())

@client.event
async def on_ready():
    print(f'Logged on as {client.user}!')

    client.default_guild_details = {
        'prefix': ['%'],
        'mod_roles': [],
        'bot_role': 0,
        'logging_channel': [0, 0]
    }

    try:
        with open('db/guilds.json', 'r') as f:
            details = json.load(f)
        for guild in details:
            for key in client.default_guild_details:
                if key not in details[guild]:
                    details[guild][key] = client.default_guild_details[key]
        with open('db/guilds.json', 'w') as f:
            json.dump(details, f)
    except FileNotFoundError:
        # Creates the guilds.json file if it doesn't exist, as it is essential for many cogs' functioning
        data = dict([(guild.id, client.default_guild_details) for guild in client.guilds])
        with open('db/guilds.json', 'w') as f:
            json.dump(data, f)

    # Loads all the cogs
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            client.load_extension(f'cogs.{filename[:-3]}')
    print('Cogs loaded successfully!\n')

client.run(os.getenv('BOT_TOKEN'))
