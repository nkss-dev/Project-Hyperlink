import discord, json, sqlite3
from datetime import datetime
from discord.ext import commands

def verificationCheck(ctx):
    return ctx.bot.verificationCheck(ctx)

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open('db/emojis.json', 'r') as f:
            self.emojis = json.load(f)['utility']

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

    def cog_check(self, ctx):
        return self.bot.basicVerificationCheck(ctx)

    @commands.command(name='profile', brief='Displays details of the user', aliases=['p'])
    async def profile(self, ctx, *, member: discord.Member=None):
        """Displays details of the user related to the server and the college"""
        member = member or ctx.author
        if not await self.check(ctx, member):
            return
        # Gets details of requested user from the database
        self.c.execute('SELECT Roll_Number, Section, SubSection, Name, Institute_Email, Verified FROM main where Discord_UID = (:uid)', {'uid': member.id})
        tuple = self.c.fetchone()
        # Exit if the user was not found
        if not tuple:
            await ctx.reply('The requested record wasn\'t found!')
            return
        # Creates a list of role objects of the user to display in the embed
        ignored_roles = [tuple[1], tuple[2], '@everyone']
        user_roles = [role.mention for role in member.roles if role.name not in ignored_roles]
        user_roles.reverse()
        user_roles = ', '.join(user_roles)
        if not user_roles:
            user_roles = 'None taken'
        # Checking if the user has a verified email or not
        status = ' '
        if tuple[5] == 'True':
            status += self.emojis['verified']
        else:
            status += self.emojis['not-verified']
        # Creating the embed
        embed = discord.Embed(
            title = ' '.join([word[:1] + word[1:].lower() for word in tuple[3].split(' ')]) + status,
            description = f'**Roll Number:** {tuple[0]}'
            + f'\n**Section:** {tuple[1]}{tuple[2][4:]}'
            + f'\n**Roles:** {user_roles}'
            + f'\n**Email:** {tuple[4]}',
            colour = member.top_role.color
        )
        embed.set_author(name = f'{member}\'s Profile', icon_url = member.avatar_url)
        embed.set_thumbnail(url = member.avatar_url)
        join_date = member.joined_at.strftime('%b %d, %Y')
        embed.set_footer(text = f'Joined at: {join_date}')
        await ctx.send(embed=embed)

    @commands.command(name='nick', brief='Nicks a user to their first name')
    @commands.bot_has_permissions(manage_nicknames=True)
    @commands.check(verificationCheck)
    async def nick(self, ctx, member: discord.Member=None):
        """Enter a member to change their name or leave it blank to change your own"""

        if member and member != ctx.author:
            if not member.guild_permissions.manage_nicknames:
                raise commands.MissingPermissions((discord.Permissions.manage_nicknames))

        else:
            if not (member := ctx.author).guild_permissions.change_nickname:
                raise commands.MissingPermissions((discord.Permissions.change_nickname))

        self.c.execute('SELECT Name from main where Discord_UID = (:uid)', {'uid': member.id})
        tuple = self.c.fetchone()

        # Exit if the user was not found
        if not tuple:
            embed = discord.Embed(
                description = f'{member.mention} does not exist in the database',
                color = discord.Color.blurple()
            )
            await ctx.reply(embed=embed)
            return

        old_nick = member.nick
        first_name = tuple[0].split(' ', 1)[0]
        await member.edit(nick = first_name[:1] + first_name[1:].lower())
        embed = discord.Embed(
            description = f'{member.mention}\'s nick changed from `{old_nick}` to `{member.nick}` successfully.',
            color = discord.Color.blurple()
        )
        await ctx.reply(embed=embed)

    @commands.command(brief='Segregated display of the number of members')
    async def memlist(self, ctx, batch: int):
        """Displays the total number of members joined/remaining/verified members per section,
        and their totals
        """

        sections = ['CE-A', 'CE-B', 'CE-C', 'CS-A', 'CS-B', 'EC-A', 'EC-B', 'EC-C', 'EE-A', 'EE-B', 'EE-C', 'IT-A', 'IT-B', 'ME-A', 'ME-B', 'ME-C', 'PI-A', 'PI-B']
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
        servers = ['NITKKR\'24: https://discord.gg/4eF7R6afqv',
            'kkr++: https://discord.gg/epaTW7tjYR'
        ]
        embed = discord.Embed(
            title = 'Invites:',
            description = '\n'.join(servers),
            color = discord.Color.blurple()
        )
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Info(bot))
