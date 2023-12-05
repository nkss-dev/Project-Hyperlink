import config
import discord
from discord.ext import commands

from base.cog import HyperlinkCog


class Mod(HyperlinkCog):
    """Moderator-only commands"""

    async def cog_check(self, ctx) -> bool:
        if not ctx.guild:
            raise commands.NoPrivateMessage
        self.l10n = await self.bot.get_l10n(ctx.guild.id)
        return super().cog_check(ctx)

    @commands.group(invoke_without_command=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def role(self, ctx, role: discord.Role, member: discord.Member):
        """Add/remove a role from a member"""
        if role in member.roles:
            await member.remove_roles(role)
            str = "remove"
        else:
            await member.add_roles(role)
            str = "add"

        embed = discord.Embed(
            description=self.l10n.format_value(
                f"role-{str}-success", {"role": role.mention, "member": member.mention}
            ),
            color=discord.Color.blurple(),
        )
        await ctx.send(embed=embed)

    @role.command(aliases=["m", "many"])
    async def multiple(
        self,
        ctx,
        roles: commands.Greedy[discord.Role],
        members: commands.Greedy[discord.Member],
    ):
        """Add roles to a number of members.

        Parameters
        ------------
        `roles`: list[discord.Role]
            The roles to be added to each member. This can be the role's ID, \
            name or tag. All roles until the first member will be inputted into this list.
        `members`: list[discord.Member]
            The members on which the roles need to be added. This can be the \
            member's ID, name or tag.
        """
        await ctx.message.add_reaction(config.emojis["loading"])

        roles = [role for role in roles if role < ctx.guild.me.top_role]

        for member in members:
            await member.add_roles(*roles)
        count = {"role_count": len(roles), "mem_count": len(members)}
        await ctx.send(self.l10n.format_value("add-roles-successful", count))

        await ctx.message.remove_reaction(config.emojis["loading"], self.bot.user)

    @role.command()
    async def roll(
        self,
        ctx,
        roles: commands.Greedy[discord.Role],
        roll_numbers: commands.Greedy[int],
    ):
        """Add roles to the given roll numbers.

        Parameters
        ------------
        `roles`: list[discord.Role]
            The roles to be added to each member. This can be the role's ID, \
            name or tag. All roles until the first member will be inputted into this list.
        `roll_numbers`: list[int]
            The roll numbers of the members on which the roles need to be added.
        """
        await ctx.message.add_reaction(config.emojis["loading"])

        count = 0
        for roll in roll_numbers:
            discord_id = await self.bot.pool.fetchval(
                "SELECT discord_uid FROM student WHERE roll_number = $1", roll
            )
            if discord_id and (member := ctx.guild.get_member(discord_id[0])):
                await member.add_roles(*roles)
                count += 1
            else:
                print(roll, end=" ")
        count = {"role_count": len(roles), "mem_count": count}
        await ctx.send(self.l10n.format_value("add-roles-successful", count))

        await ctx.message.remove_reaction(config.emojis["loading"], self.bot.user)


async def setup(bot):
    await bot.add_cog(Mod(bot))
