import json
import sqlite3

from typing import Optional, Union
from utils.l10n import get_l10n
from utils.utils import deleteOnReaction

import discord
from discord.ext import commands

def basicVerificationCheck(ctx) -> bool:
    return ctx.bot.basicVerificationCheck(ctx)

def verificationCheck(ctx) -> bool:
    return ctx.bot.verificationCheck(ctx)

class ProfileChoice(discord.ui.View):
    """UI class for profile"""

    def __init__(self, embed, l10n, user):
        super().__init__()
        self.embed = embed
        self.l10n = l10n
        self.type = False
        self.user = user

    async def interaction_check(self, interaction) -> bool:
        """check if the interaction is authorised or not"""
        if interaction.user != self.user:
            await interaction.response.send_message(
                content=self.l10n.format_value('incorrect-user'),
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label='Hidden', style=discord.ButtonStyle.green)
    async def hidden(self, button: discord.ui.Button, interaction: discord.Interaction):
        """invoked when the `Hidden` button is clicked"""
        await interaction.response.send_message(embed=self.embed, ephemeral=True)
        await interaction.message.delete()
        self.type = False
        self.stop()

    @discord.ui.button(label='Exposed', style=discord.ButtonStyle.red)
    async def exposed(self, button: discord.ui.Button, interaction: discord.Interaction):
        """invoked when the `Exposed` button is clicked"""
        await interaction.message.delete()
        self.type = True
        self.stop()

class Info(commands.Cog):
    """Information commands"""

    def __init__(self, bot):
        self.bot = bot

        with open('db/emojis.json') as f:
            self.emojis = json.load(f)['utility']

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

    async def getProfileEmbed(self, ctx, member) -> Optional[discord.Embed]:
        """Return the details of the given user in an embed"""
        member_guild = ctx.guild and isinstance(member, discord.Member)

        tuple = self.c.execute(
            'select Roll_Number, Section, SubSection, Name, Institute_Email, Verified from main where Discord_UID = (:uid)',
            {'uid': member.id}
        ).fetchone()

        if not tuple:
            await ctx.reply(self.l10n.format_value('record-notfound'))
            return

        if member_guild:
            ignored_roles = [tuple[1], tuple[2], '@everyone']
            user_roles = [role.mention for role in member.roles if role.name not in ignored_roles]
            user_roles.reverse()
            if not (user_roles := ', '.join(user_roles)):
                user_roles = self.l10n.format_value('roles-none')
        else:
            user_roles = self.l10n.format_value('roles-none')

        if tuple[5] == 'True':
            status = self.emojis['verified']
        else:
            status = self.emojis['not-verified']

        profile = {
            'roll': str(tuple[0]),
            'section': tuple[1] + tuple[2][4],
            'roles': user_roles,
            'email': tuple[4]
        }
        embed = discord.Embed(
            title = f'{tuple[3].title()} {status}',
            description = self.l10n.format_value('profile', profile),
            color = member.top_role.color if member_guild else discord.Color.blurple()
        )
        embed.set_author(
            name = self.l10n.format_value('profile-name', {'member': str(member)}),
            icon_url = member.display_avatar.url
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        if member_guild:
            embed.set_footer(text=self.l10n.format_value(
                'profile-join-date',
                {'date': member.joined_at.strftime('%b %d, %Y')})
            )

        return embed

    def cog_check(self, ctx) -> bool:
        self.l10n = get_l10n(ctx.guild.id if ctx.guild else 0, 'info')
        return self.bot.basicVerificationCheck(ctx)

    @commands.command(aliases=['p'])
    @commands.check(basicVerificationCheck)
    async def profile(self, ctx, *, member: Union[discord.Member, discord.User]=None):
        """Show the user's profile in an embed.

        The embed contains details related to both, the server and the college.
        The user is given a choice between keeping the profile hidden or visible. \
        If the command is invoked in a DM channel, the choice defaults to visible.

        Parameters
        ------------
        `member`: Optional[discord.Member]
            The member whose profile is displayed. If this is specified, \
            a check is performed to see if the author of the command is \
            authorised to view another user's profile. If left blank, the \
            member defaults to the author of the command.
        """
        member = member or ctx.author
        if member != ctx.author:
            await self.bot.moderatorCheck(ctx)

        if not (embed := await self.getProfileEmbed(ctx, member)):
            return

        if ctx.guild:
            view = ProfileChoice(embed, self.l10n, ctx.author)
            await ctx.send(self.l10n.format_value('choice'), view=view)
            await view.wait()

            if view.type:
                message = await ctx.send(embed=embed)
            else:
                await ctx.message.delete()
                return
        else:
            message = await ctx.send(embed=embed)
        await deleteOnReaction(ctx, message)

    @commands.command()
    @commands.bot_has_permissions(manage_nicknames=True)
    @commands.check(verificationCheck)
    @commands.guild_only()
    async def nick(self, ctx, *, member: discord.Member=None):
        """Change the nick of a user to their first name.

        Parameters
        ------------
        `member`: Optional[discord.Member]
            The member whose nick is to be changed. If this is specified, \
            a check is performed to see if the author of the command is \
            authorised to change another user's nickname.
            If left blank, the member defaults to the author of the command.
        """

        member = member or ctx.author
        if await self.bot.is_owner(member):
            pass
        elif member != ctx.author:
            if not ctx.author.guild_permissions.manage_nicknames:
                raise commands.MissingPermissions([discord.Permissions.manage_nicknames])
        else:
            if not member.guild_permissions.change_nickname:
                raise commands.MissingPermissions([discord.Permissions.change_nickname])

        name = self.c.execute(
            'select Name from main where Discord_UID = (:uid)',
            {'uid': member.id}
        ).fetchone()

        if not name:
            embed = discord.Embed(
                description = self.l10n.format_value('member-notfound', {'member': member.mention}),
                color = discord.Color.blurple()
            )
            await ctx.reply(embed=embed)
            return

        old_nick = member.nick
        first_name = name[0].split(' ', 1)[0].capitalize()
        await member.edit(nick=first_name)

        nick = {
            'member': member.mention,
            'old': f'{old_nick}',
            'new': member.nick
        }
        embed = discord.Embed(
            description = self.l10n.format_value('nick-change-success', nick),
            color = discord.Color.blurple()
        )
        await ctx.reply(embed=embed)

    @commands.command()
    @commands.check(verificationCheck)
    async def memlist(self, ctx, batch: int):
        """Show the stats of students of the specified batch.

        The displayed table has 3 value columns and is separated by sub-sections
        Columns:
            `Joined`: Represents users that have linked their Discord account \
                with a student's details in the database.
            `Remaining`: Represents users that have not linked their Discord \
                account with a student's details in the database.
            `Verified`: Represents users whose identities have been confirmed.

        Parameters
        ------------
        `batch`: <class 'int'>
            The batch for which the stats are shown.
        """

        sections = (
            'CE-A', 'CE-B', 'CE-C',
            'CS-A', 'CS-B',
            'EC-A', 'EC-B', 'EC-C',
            'EE-A', 'EE-B', 'EE-C',
            'IT-A', 'IT-B',
            'ME-A', 'ME-B', 'ME-C',
            'PI-A', 'PI-B'
        )
        total = []
        joined = []
        verified = []

        for section in sections:
            tuple = self.c.execute(
                'select count(*), count(Discord_UID) from main where Section = (:section) and Batch = (:batch)',
                {'section': section, 'batch': batch}
            ).fetchone()
            total.append(tuple[0])
            joined.append(tuple[1])

        for section in sections:
            countVerified = self.c.execute(
                'select count(*) from main where Section = (:section) and Verified = "True" and Batch = (:batch)',
                {'section': section, 'batch': batch}
            ).fetchone()[0]
            verified.append(countVerified)

        tuple = self.c.execute(
            'select count(*), count(Discord_UID) from main where Batch = (:batch)',
            {'batch': batch}
        ).fetchone()
        total.append(tuple[0])
        joined.append(tuple[1])

        table =  '╭─────────┬────────┬───────────┬──────────╮\n'
        table += '│ Section │ Joined │ Remaining │ Verified │\n'
        table += '├─────────┼────────┼───────────┼──────────┤\n'
        previous = sections[0][:2]
        for section, num1, num2, verify in zip(sections, joined, total, verified):
            if section[:2] != previous[:2]:
                table += '├─────────┼────────┼───────────┼──────────┤\n'
            table += '│{:^9}│{:^8}│{:^11}│{:^10}│\n'.format(section, str(num1).zfill(2), str(num2-num1).zfill(2), str(verify).zfill(2))
            previous = section[:2]
        table += '├─────────┼────────┼───────────┼──────────┤\n'
        table += '│  Total  │{:^8}│{:^11}│{:^10}│\n'.format(str(sum(joined[:-1])).zfill(2), str(sum(total[:-1])-sum(joined[:-1])).zfill(2), str(sum(verified)).zfill(2))
        table += '╰─────────┴────────┴───────────┴──────────╯'

        embed = discord.Embed(
            description = f'```\n{table}```',
            color = discord.Color.blurple()
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=['inv'])
    async def invite(self, ctx):
        """Send the invite of some Discord servers"""
        servers = (
            'NITKKR\'24: https://discord.gg/4eF7R6afqv',
            'kkr++: https://discord.gg/epaTW7tjYR'
        )

        embed = discord.Embed(
            title = self.l10n.format_value('invite'),
            description = '\n'.join(servers),
            color = discord.Color.blurple()
        )
        await ctx.send(embed=embed)

def setup(bot):
    """invoked when this file is attempted to be loaded as an extension"""
    bot.add_cog(Info(bot))
