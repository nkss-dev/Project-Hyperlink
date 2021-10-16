import config
import re

from discord import Intents
from discord.ext import commands
from utils.constructor import Constructor


def get_prefix(_, message) -> str:
    """return the bot's prefix for a guild or a DM"""
    if message.guild:
        return client.guild_data[str(message.guild.id)]['prefix']
    return '%'


client = commands.Bot(
    command_prefix=get_prefix,
    intents=Intents.all(),
    owner_ids=config.owner_ids
)


@client.event
async def on_ready():
    """invoked when the bot logs in successfully"""
    Constructor(client)


@client.before_invoke
async def bracketCheck(ctx):
    if re.search(r'<.+>', ctx.message.content):
        raise commands.CheckFailure('AngularBracketsNotAllowed')

client.run(config.bot_token)
