import config

from discord.ext import commands


def is_exists():
    """Check if the user has completed basic verification"""
    async def pred(ctx):
        verified = await ctx.bot.conn.fetchval(
            '''
            SELECT
                exists (
                    SELECT
                        verified
                    FROM
                        student
                    WHERE
                        discord_uid = $1
                )
            ''', ctx.author.id
        )

        if not verified:
            raise commands.CheckFailure('AccountNotLinked')
        return True
    return commands.check(pred)


def is_verified():
    """Check if the user's identity has been verified"""
    async def pred(ctx):
        verified = await ctx.bot.conn.fetch(
            'SELECT verified FROM student WHERE discord_uid = $1',
            ctx.author.id
        )

        if not verified:
            raise commands.CheckFailure('AccountNotLinked')
        if not verified[0]['verified']:
            raise commands.CheckFailure('UserNotVerified')
        return True
    return commands.check(pred)


def is_mod():
    """Check if the user is a moderator"""
    async def pred(ctx):
        if not is_verified():
            return False

        if await ctx.bot.is_owner(ctx.author):
            return True
        if ctx.author.guild_permissions.administrator:
            return True

        # Fetches the moderator roles set for the guild
        mod_roles = await ctx.bot.conn.fetch(
            'SELECT role FROM mod_role WHERE id = $1', ctx.guild.id
        )
        if mod_roles:
            mod_roles = [role['role'] for role in mod_roles]
            await commands.has_any_role(*mod_roles).predicate(ctx)
        else:
            raise commands.CheckFailure('MissingModeratorRoles')
        return True
    return commands.check(pred)


def is_authorised():
    """Check if the user is authorised to access the bot's database"""
    async def pred(ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True
        if ctx.author.id in config.authorised_ids:
            return True

        raise commands.CheckFailure('MissingAuthorisation')
    return commands.check(pred)