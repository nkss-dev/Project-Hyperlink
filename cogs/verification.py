import config
import json
import re

from asyncio import TimeoutError
from utils.l10n import get_l10n
from utils.utils import generateID

import discord
from discord.ext import commands

import smtplib
from email.message import EmailMessage


def basicVerificationCheck(ctx):
    return ctx.bot.basicVerificationCheck(ctx)


class Verify(commands.Cog):
    """Verification management"""

    def __init__(self, bot):
        self.bot = bot

        with open('db/codes.json') as codes:
            self.codes = json.load(codes)
        with open('db/emojis.json') as emojis:
            self.emojis = json.load(emojis)['utility']

        self.sections = (
            'CE-A', 'CE-B', 'CE-C',
            'CS-A', 'CS-B',
            'EC-A', 'EC-B', 'EC-C',
            'EE-A', 'EE-B', 'EE-C',
            'IT-A', 'IT-B',
            'ME-A', 'ME-B', 'ME-C',
            'PI-A', 'PI-B'
        )

    async def sendEmail(self, ctx, name: str, email: str, manual=True):
        """Send a verification email to the given email"""
        await ctx.message.add_reaction(self.emojis['loading'])

        otp = generateID(seed='01234567890123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ')

        # Creating the email
        msg = EmailMessage()
        msg['Subject'] = f'Verification of {ctx.author} in {ctx.guild}'
        msg['From'] = config.email
        msg['To'] = email

        if manual:
            command = f'{ctx.clean_prefix}{ctx.command.parent} code {otp}'
        else:
            command = otp
        variables = {
            '{$user}': name,
            '{$otp}': otp,
            '{$guild}': ctx.guild.name,
            '{$channel}': f'https://discord.com/channels/{ctx.guild.id}/{ctx.channel.id}',
            '{$command}': command
        }
        with open('utils/verification.html') as f:
            html = f.read()
        html = re.sub(r'({\$\w+})', lambda x: variables[x.group(0)], html)
        msg.set_content(html, subtype='html')

        # Sending the email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(config.email, config.password_token)
            smtp.send_message(msg)

        await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)

        self.codes[str(ctx.author.id)] = otp
        self.save()

    def checkCode(self, author_id: str, code: str) -> bool:
        """Check if the entered code matches the OTP"""
        if not self.codes[str(author_id)] == code:
            return False

        del self.codes[str(author_id)]
        self.save()

        # Marks user as verified in the database
        self.bot.c.execute(
            'update main set Verified = "True" where Discord_UID = (:uid)',
            {'uid': author_id}
        )
        self.bot.db.commit()
        return True

    @commands.group()
    @commands.guild_only()
    async def verify(self, ctx):
        """Command group for verification functionality"""
        self.l10n = get_l10n(ctx.guild.id, 'verification')

        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)
            return

        verified = self.bot.c.execute(
            'select Verified from main where Discord_UID = (:uid)',
            {'uid': ctx.author.id}
        ).fetchone()

        if verified:
            if verified[0] == 'False':
                if ctx.invoked_subcommand.name == 'basic':
                    raise commands.CheckFailure('AccountAlreadyLinked')
            else:
                raise commands.CheckFailure('UserAlreadyVerified')

    @verify.command()
    async def basic(self, ctx, section: str, roll_no: int):
        """Link a Discord account to a record in the database.

        Parameters
        ------------
        `section`: <class 'str'>
            The section the student is in. Must be either of the following:
                CE-A, CE-B, CE-C,
                CS-A, CS-B,
                EC-A, EC-B, EC-C,
                EE-A, EE-B, EE-C,
                IT-A, IT-B,
                ME-A, ME-B, ME-C,
                PI-A, PI-B

        `roll_no`: <class 'int'>
            The roll number of the student.
        """
        tuple = self.bot.c.execute(
            'select Section, Subsection, Name, Institute_Email, Batch, Discord_UID, Guilds from main where Roll_Number = (:roll)',
            {'roll': roll_no}
        ).fetchone()

        if not tuple:
            await ctx.reply(self.l10n.format_value('verify-basic-record-notfound'))
            return

        override = False
        if details := self.bot.guild_data[str(ctx.guild.id)].get('verification'):
            if tuple[4] != details['batch']:
                await ctx.reply(self.l10n.format_value(
                        'incorrect-server', {'batch': int(tuple[4])}))
                return
        else:
            await ctx.reply(self.l10n.format_value('server-not-allowed'))

            def check_owner(msg):
                return msg.author.id in self.bot.owner_ids and msg.channel == ctx.channel

            try:
                message = await self.bot.wait_for(
                    'message', timeout=60.0, check=check_owner)
                if message.content.lower() == 'override':
                    override = True
            except TimeoutError:
                return

        if section not in self.sections:
            await ctx.reply(self.l10n.format_value(
                    'verify-basic-section-notfound', {'section': section}))
            return

        if section != tuple[0]:
            await ctx.reply(
                self.l10n.format_value('verify-basic-section-mismatch'))
            return

        if user := ctx.guild.get_member(tuple[5]):
            await self.sendEmail(ctx, tuple[2].title().strip(), tuple[3], False)
            await ctx.reply(self.l10n.format_value(
                    'verify-basic-already-claimed',
                    {'user': f'{user}', 'email': tuple[3]}))

            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel

            while True:
                try:
                    ctx.message = await self.bot.wait_for(
                        'message', timeout=120.0, check=check)
                    if self.checkCode(ctx.author.id, ctx.message.content):
                        self.bot.c.execute(
                            'update main set Verified = "True" where Roll_Number = (:roll)',
                            {'roll': roll_no}
                        )
                        await user.kick(reason=self.l10n.format_value(
                                'member-kick-old',
                                {'user': ctx.author.mention}))
                        break

                    await ctx.reply(self.l10n.format_value(
                            'verify-code-retry',
                            {'code': ctx.message.content}))
                except TimeoutError:
                    await ctx.send(self.l10n.format_value('react-timeout'))
                    return

        # Assigning section/sub-section roles to the user
        if role := discord.utils.get(ctx.guild.roles, name=tuple[0]):
            await ctx.author.add_roles(role)
        if role := discord.utils.get(ctx.guild.roles, name=tuple[1]):
            await ctx.author.add_roles(role)

        await ctx.reply(self.l10n.format_value('verify-basic-success'))

        # Removing restricting role
        role_id = self.bot.guild_data[str(ctx.guild.id)]['verification']['role']
        if role := ctx.guild.get_role(role_id):
            await ctx.author.remove_roles(role)

        # Input changes to the database
        guilds = json.loads(tuple[6])
        if not override and ctx.guild.id not in guilds:
            guilds.append(ctx.guild.id)
        guilds = json.dumps(guilds)

        self.bot.c.execute(
            'update main set Discord_UID = (:uid), Guilds = (:guilds) where Roll_Number = (:roll)',
            {'uid': ctx.author.id, 'roll': roll_no, 'guilds': guilds}
        )
        self.bot.db.commit()

        first_name = tuple[2].split(' ', 1)[0].capitalize()
        await ctx.author.edit(nick=first_name)

    @verify.command()
    @commands.check(basicVerificationCheck)
    async def email(self, ctx, email: str):
        """Verify the user's identity by verifying their institute email.

        Parameters
        ------------
        `email`: <class 'str'>
            The institute email of the user.
        """
        tuple = self.bot.c.execute(
            'select Name, Institute_Email from main where Discord_UID = (:uid)',
            {'uid': ctx.author.id}
        ).fetchone()

        if email.lower() != tuple[1]:
            await ctx.reply(self.l10n.format_value('verify-email-mismatch'))
            return

        await self.sendEmail(ctx, tuple[0].title().strip(), tuple[1])

        await ctx.reply(self.l10n.format_value('verify-check-email', {'prefix': ctx.prefix}))

    @verify.command()
    @commands.check(basicVerificationCheck)
    async def code(self, ctx, code: str):
        """Check if the inputted code matches the sent OTP.

        Parameters
        ------------
        `code`: <class 'str'>
            The code to be checked
        """
        if str(ctx.author.id) not in self.codes:
            await ctx.reply(self.l10n.format_value('verify-not-received'))
            return

        if self.checkCode(ctx.author.id, code):
            await ctx.reply(self.l10n.format_value('verify-email-success', {'emoji': self.emojis['verified']}))
        else:
            await ctx.reply(self.l10n.format_value('verify-code-incorrect'))

    def save(self):
        """Save the data to a json file"""
        with open('db/codes.json', 'w') as f:
            json.dump(self.codes, f)


def setup(bot):
    """Called when this file is attempted to be loaded as an extension"""
    bot.add_cog(Verify(bot))
