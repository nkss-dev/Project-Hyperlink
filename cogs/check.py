import json
import sqlite3

from discord.ext import commands

class Check(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

        self.bot.moderatorCheck = self.moderatorCheck
        self.bot.basicVerificationCheck = self.basicVerificationCheck
        self.bot.verificationCheck = self.verificationCheck

    def basicVerificationCheck(self, ctx):
        verified = self.c.execute(
            'select Verified from main where Discord_UID = (:uid)',
            {'uid': ctx.author.id}
        ).fetchone()

        if not verified:
            raise commands.CheckFailure('AccountNotLinked')
        else:
            return True

    def verificationCheck(self, ctx):
        verified = self.c.execute(
            'select Verified from main where Discord_UID = (:uid)',
            {'uid': ctx.author.id}
        ).fetchone()

        if not verified:
            raise commands.CheckFailure('AccountNotLinked')
        if verified[0] == 'False':
            raise commands.CheckFailure('UserNotVerified')
        return True

    async def moderatorCheck(self, ctx):
        if not self.verificationCheck(ctx):
            return False

        if await self.bot.is_owner(ctx.author) or ctx.author == ctx.guild.owner:
            return True

        with open('db/guilds.json', 'r') as f:
            guild_data = json.load(f)

        # Fetches the moderator roles set for the guild
        if mod_roles := guild_data[str(ctx.guild.id)]['mod_roles']:
            await commands.has_any_role(*mod_roles).predicate(ctx)
        else:
            raise commands.CheckFailure('MissingModeratorRoles')

        return True

def setup(bot):
    bot.add_cog(Check(bot))
