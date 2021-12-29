import json
from datetime import datetime
from typing import Union

import discord
from discord.ext import commands
from tabulate import tabulate

from utils import checks
from utils.l10n import get_l10n
from utils.utils import deleteOnReaction, is_alone


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

    async def get_profile_embed(self, guild: bool, member) -> discord.Embed:
        """Return the details of the given user in an embed"""
        details = self.bot.c.execute(
            '''select Roll_Number, Section, SubSection, Name,
                Mobile, Birthday, Institute_Email, Hostel_Number, Verified
                from main where Discord_UID = ?
            ''', (member.id,)
        ).fetchone()

        if not details:
            return discord.Embed()

        # Set variables based on context
        if guild and isinstance(member, discord.Member):
            color = member.color
        else:
            color = discord.Color.blurple()

        # Set emoji based on verification status
        status = 'verified' if details[8] else 'not-verified'

        # Fetch member's groups
        _groups = self.bot.c.execute(
            '''select Name, Alias, Server_Invite, Guest_Role
                from group_discord_users where Discord_UID = ?
            ''', (member.id,)
        ).fetchall()
        groups = []
        group_names = []
        for full_name, alias, invite, role in _groups:
            name = alias or full_name
            group_names.append(name)
            if invite and role:
                hovertext = f'Click here to join the official {name} server'
                text = f'[{name}](https://discord.gg/{invite} "{hovertext}")'
            else:
                text = name
            groups.append(text)

        # Generating the embed
        embed = discord.Embed(
            title=f'{details[3]} {self.emojis[status]}',
            color=color
        )
        embed.set_author(
            name=self.l10n.format_value('profile-name', {'member': str(member)}),
            icon_url=member.display_avatar.url
        )
        embed.set_thumbnail(url=member.display_avatar.url)

        # Add generic student details
        if hostel := details[7]:
            hostel_name = self.bot.c.execute(
                'select Hostel_Name from hostels where Hostel_Number = ?',
                (details[7],)
            ).fetchone()
            hostel = f'{details[7]} - {hostel_name}'

        fields = {
            'roll': details[0],
            'sec': details[1] + details[2][4],
            'email': details[6],
            'hostel': hostel,
            'groups': ', '.join(groups) or self.l10n.format_value('no-group'),
        }
        if details[4]:
            fields['mob'] = details[4]
        if details[5]:
            dt = datetime.strptime(details[5], '%Y-%m-%d')
            fields['bday'] = discord.utils.format_dt(dt, style='D')

        for name, value in fields.items():
            embed.add_field(name=self.l10n.format_value(name), value=value)

        # Fetch member roles
        user_roles = []
        if guild:
            ignored_roles = [*details[1:3], details[7], *group_names, '@everyone']
            for role in member.roles:
                try:
                    ignored_roles.remove(role.name)
                except ValueError:
                    user_roles.append(role.mention)
            if user_roles:
                user_roles = ', '.join(user_roles[::-1])

        # Add field displaying the user's server/Discord join date
        if guild and user_roles:
            embed.add_field(
                name=self.l10n.format_value('roles'),
                value=user_roles
            )

        join_dt = member.joined_at if guild else member.created_at
        embed.add_field(
            name=self.l10n.format_value('join'),
            value=discord.utils.format_dt(join_dt, style='D'),
            inline=False
        )

        return embed

    async def cog_check(self, ctx) -> bool:
        self.l10n = get_l10n(ctx.guild.id if ctx.guild else 0, 'info')
        return await checks.is_exists().predicate(ctx)

    @commands.command(aliases=['p'])
    async def profile(self, ctx, *, member: Union[discord.Member, discord.User] = None):
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
        if member is None:
            member = ctx.author
        else:
            await checks.is_authorised().predicate(ctx)

        embed = await self.get_profile_embed(bool(ctx.guild), member)
        if not embed:
            ctx.author = member
            raise commands.CheckFailure('RecordNotFound')

        if not await is_alone(ctx.channel, ctx.author, self.bot.user):
            view = ProfileChoice(embed, self.l10n, ctx.author)
            await ctx.send(self.l10n.format_value('choice'), view=view)
            await view.wait()

            if view.type:
                embed.set_footer(text=self.l10n.format_value('footer'))
                message = await ctx.send(embed=embed)
            else:
                await ctx.message.delete()
                return
        else:
            message = await ctx.send(embed=embed)
        await deleteOnReaction(ctx, message)

    @commands.command()
    @commands.bot_has_permissions(manage_nicknames=True)
    @checks.is_verified()
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
                raise commands.MissingPermissions(['manage_nicknames'])
        else:
            if not member.guild_permissions.change_nickname:
                raise commands.MissingPermissions(['change_nickname'])

        name = self.bot.c.execute(
            'select Name from main where Discord_UID = ?', (member.id,)
        ).fetchone()

        if not name:
            ctx.author = member
            raise commands.CheckFailure('RecordNotFound')

        old_nick = member.nick
        first_name = name.split(' ', 1)[0]
        await member.edit(nick=first_name)

        nick = {
            'member': member.mention,
            'old': f'{old_nick}',
            'new': first_name
        }
        embed = discord.Embed(
            description=self.l10n.format_value('nick-change-success', nick),
            color=discord.Color.blurple()
        )
        await ctx.reply(embed=embed)

    @commands.command()
    @checks.is_verified()
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
        sections = self.bot.c.execute(
            '''select Section, count(Discord_UID),
                count(*) - count(Discord_UID), count(Verified)
                from main where Batch = ? group by Section;
            ''', (batch,)
        ).fetchall()

        # Get the indices of the rows to be deleted
        indices = []
        previous = sections[0][0]
        for i, section in zip(range(2, len(sections)*2, 2), sections):
            if section[0][:2] == previous[:2]:
                indices.append(i + 2)
            else:
                indices[-1] += 2
            previous = section[0]

        # Get total values for each numerical column
        counts = [row[1:] for row in sections]
        total = [sum(count) for count in zip(*counts)]

        table = tabulate(
            [*sections, ['Total', *total]],
            headers=('Section', 'Joined', 'Remaining', 'Verified'),
            tablefmt='grid'
        ).split('\n')
        table[2] = table[0]

        # Delete the extra dashed lines
        for i, index in enumerate(indices):
            table.pop(index - i)
        table = '\n'.join(table)

        embed = discord.Embed(
            description=f'```swift\n{table}```',
            color=discord.Color.blurple()
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
    bot.add_cog(Info(bot))