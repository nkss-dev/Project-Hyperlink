from discord import Intents
from discord.ext.commands import Bot
from utils.constructor import Constructor

import os
from dotenv import load_dotenv
load_dotenv()

def get_prefix(_, message) -> str:
    """return the bot's prefix for a guild or a DM"""
    if message.guild:
        return client.guild_data[str(message.guild.id)]['prefix']
    return '%'

client = Bot(
    command_prefix=get_prefix,
    intents=Intents.all(),
    owner_ids=list(map(int, os.environ['OWNER_IDS'].split(', ')))
)

@client.event
async def on_ready():
    """invoked when the bot logs in successfully"""
    Constructor(client)

client.run(os.environ['BOT_TOKEN'])
