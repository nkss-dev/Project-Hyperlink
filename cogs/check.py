from discord.ext import commands


class Check(commands.Cog):
    """Checks used in the bot"""

    def __init__(self, bot):
        self.bot = bot

        self.bot.moderatorCheck = self.moderatorCheck
        self.bot.basicVerificationCheck = self.basicVerificationCheck
        self.bot.verificationCheck = self.verificationCheck

    def basicVerificationCheck(self, ctx) -> bool:
        """Check if the user has completed basic verification"""
        verified = self.bot.c.execute(
            'select Verified from main where Discord_UID = ?', (ctx.author.id,)
        ).fetchone()

        if not verified:
            raise commands.CheckFailure('AccountNotLinked')

        return True

    def verificationCheck(self, ctx) -> bool:
        """Check if the user's identity has been verified"""
        verified = self.bot.c.execute(
            'select Verified from main where Discord_UID = ?', (ctx.author.id,)
        ).fetchone()

        if not verified:
            raise commands.CheckFailure('AccountNotLinked')
        if not verified[0]:
            raise commands.CheckFailure('UserNotVerified')
        return True

    async def moderatorCheck(self, ctx) -> bool:
        """Check if the user is a moderator"""
        if not self.verificationCheck(ctx):
            return False

        if await self.bot.is_owner(ctx.author):
            return True
        if ctx.author.guild_permissions.administrator:
            return True

        # Fetches the moderator roles set for the guild
        mod_roles = self.bot.c.execute(
            'select prefix from prefixes where ID = ?', (ctx.guild.id,)
        ).fetchall()
        if mod_roles:
            await commands.has_any_role(*mod_roles).predicate(ctx)
        else:
            raise commands.CheckFailure('MissingModeratorRoles')

        return True


def setup(bot):
    """Called when this file is attempted to be loaded as an extension"""
    bot.add_cog(Check(bot))
