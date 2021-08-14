import json
import sqlite3
from utils.l10n import get_l10n

import discord
from discord.ext import commands

def verificationCheck(ctx):
    return ctx.bot.verificationCheck(ctx)

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open('db/emojis.json') as f:
            self.emojis = json.load(f)['utility']

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

    def cog_check(self, ctx):
        self.l10n = get_l10n(ctx.guild.id, 'info')
        return self.bot.basicVerificationCheck(ctx)

    @commands.command(brief='Displays details of the user', aliases=['p'])
    async def profile(self, ctx, *, member: discord.Member=None):
        """Displays details of the user related to the server and the college"""

        member = member or ctx.author
        if member != ctx.author:
            await self.bot.moderatorCheck(ctx)

        self.c.execute('SELECT Roll_Number, Section, SubSection, Name, Institute_Email, Verified FROM main where Discord_UID = (:uid)', {'uid': member.id})
        tuple = self.c.fetchone()

        if not tuple:
            await ctx.reply(self.l10n.format_value('record-notfound'))
            return

        ignored_roles = [tuple[1], tuple[2], '@everyone']
        user_roles = [role.mention for role in member.roles if role.name not in ignored_roles]
        user_roles.reverse()
        user_roles = ', '.join(user_roles)
        if not user_roles:
            user_roles = self.l10n.format_value('roles-none')

        status = ' '
        if tuple[5] == 'True':
            status += self.emojis['verified']
        else:
            status += self.emojis['not-verified']

        profile = {
            'roll': str(tuple[0]),
            'section': tuple[1] + tuple[2][4:],
            'roles': user_roles,
            'email': tuple[4]
        }
        embed = discord.Embed(
            title = f'{tuple[3].title()}{status}',
            description = self.l10n.format_value('profile', profile),
            colour = member.top_role.color
        )
        embed.set_author(
            name = self.l10n.format_value('profile-name', {'member': str(member)}),
            icon_url = member.avatar_url
        )
        embed.set_thumbnail(url=member.avatar_url)
        date = member.joined_at.strftime('%b %d, %Y')
        embed.set_footer(text=self.l10n.format_value('profile-join-date', {'date': date}))

        await ctx.send(embed=embed)

    @commands.command(brief='Nicks a user to their first name')
    @commands.bot_has_permissions(manage_nicknames=True)
    @commands.check(verificationCheck)
    async def nick(self, ctx, member: discord.Member=None):
        """Enter a member to change their name or leave it blank to change your own"""

        member = member or ctx.author
        if member != ctx.author:
            if not ctx.author.guild_permissions.manage_nicknames:
                raise commands.MissingPermissions([discord.Permissions.manage_nicknames])

        else:
            if not member.guild_permissions.change_nickname:
                raise commands.MissingPermissions([discord.Permissions.change_nickname])

        self.c.execute('SELECT Name from main where Discord_UID = (:uid)', {'uid': member.id})
        tuple = self.c.fetchone()

        if not tuple:
            embed = discord.Embed(
                description = self.l10n.format_value('member-notfound', {'member': member.mention}),
                color = discord.Color.blurple()
            )
            await ctx.reply(embed=embed)
            return

        old_nick = member.nick
        first_name = tuple[0].split(' ', 1)[0].capitalize()
        await member.edit(nick=first_name)

        nick = {
            'member': member.mention,
            'old': old_nick,
            'new': member.nick
        }
        embed = discord.Embed(
            description = self.l10n.format_value('nick-change-success', nick),
            color = discord.Color.blurple()
        )
        await ctx.reply(embed=embed)

    @commands.command(brief='Segregated display of the number of members')
    async def memlist(self, ctx, batch: int):
        """Displays the total number of members joined/remaining/verified members per section,
        and their totals
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
            self.c.execute('SELECT count(*), count(Discord_UID) from main where Section = (:section) and Batch = (:batch)', {'section': section, 'batch': batch})
            tuple = self.c.fetchone()
            total.append(tuple[0])
            joined.append(tuple[1])
        for section in sections:
            self.c.execute('SELECT count(*) from main where Section = (:section) and Verified = "True" and Batch = (:batch)', {'section': section, 'batch': batch})
            tuple = self.c.fetchone()
            verified.append(tuple[0])
        self.c.execute('SELECT count(*), count(Discord_UID) from main where Batch = (:batch)', {'batch': batch})
        tuple = self.c.fetchone()
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

    @commands.command(brief='Gives invites of some servers', aliases=['inv'])
    async def invite(self, ctx):
        servers = ('NITKKR\'24: https://discord.gg/nitkkr-24',
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
