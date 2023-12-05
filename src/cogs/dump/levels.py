import random
import re

import discord
from discord.ext import commands

import cogs.checks as checks


def is_emoji(message):
    if re.fullmatch(r":[a-zA-Z0-9]+:", message):
        return True
    else:
        return False


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ignore_emojis = True

        self.exists = list(
            bot.c.execute("select User_ID, Guild_ID from levels").fetchall()
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if self.ignore_emojis and is_emoji(message.content):
            return

        if checks.is_verified():
            xp = random.randint(18, 28)
        else:
            xp = random.randint(15, 25)

        ids = message.author.id, message.guild.id
        if ids not in self.exists:
            self.bot.c.execute("insert into levels values (?, ?, ?, 1)", (*ids, xp))
            self.exists.append(ids)
        else:
            self.bot.c.execute(
                """update levels set xp = xp + ?, messages = messages + 1
                    where User_ID = ? and Guild_ID = ?
                """,
                (xp, *ids),
            )
        self.bot.db.commit()


def setup(bot):
    """Called when this file is attempted to be loaded as an extension"""
    bot.add_cog(Levels(bot))
