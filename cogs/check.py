from discord.ext import commands

class Check(commands.Cog):
    """Checks used in the bot"""

    def __init__(self, bot):
        self.bot = bot

        self.bot.moderatorCheck = self.moderatorCheck
        self.bot.basicVerificationCheck = self.basicVerificationCheck
        self.bot.verificationCheck = self.verificationCheck

    def basicVerificationCheck(self, ctx) -> bool:
        """check if the user has completed basic verification"""
        verified = self.bot.c.execute(
            'select Verified from main where Discord_UID = (:uid)',
            {'uid': ctx.author.id}
        ).fetchone()

        if not verified:
            raise commands.CheckFailure('AccountNotLinked')

        return True

    def verificationCheck(self, ctx) -> bool:
        """check if the user's identity has been verified"""
        verified = self.bot.c.execute(
            'select Verified from main where Discord_UID = (:uid)',
            {'uid': ctx.author.id}
        ).fetchone()

        if not verified:
            raise commands.CheckFailure('AccountNotLinked')
        if verified[0] == 'False':
            raise commands.CheckFailure('UserNotVerified')
        return True

    async def moderatorCheck(self, ctx) -> bool:
        """check if the user is a moderator"""
        if not self.verificationCheck(ctx):
            return False

        if await self.bot.is_owner(ctx.author) or ctx.author == ctx.guild.owner:
            return True

        # Fetches the moderator roles set for the guild
        if mod_roles := self.bot.guild_data[str(ctx.guild.id)]['roles']['mod']:
            await commands.has_any_role(*mod_roles).predicate(ctx)
        else:
            raise commands.CheckFailure('MissingModeratorRoles')

        return True

def setup(bot):
    """invoked when this file is attempted to be loaded as an extension"""
    bot.add_cog(Check(bot))
