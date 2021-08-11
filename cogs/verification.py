import json
import math
import os
import random
import sqlite3
from utils.l10n import l10n

from discord.ext import commands
from discord import utils

import smtplib
from email.message import EmailMessage

from dotenv import load_dotenv
load_dotenv()

def basicVerificationCheck(ctx):
    return ctx.bot.basicVerificationCheck(ctx)

class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

        try:
            with open('db/codes.json') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {}
        with open('db/emojis.json') as f:
            self.emojis = json.load(f)['utility']

        self.sections = (
            'CE-A', 'CE-B', 'CE-C',
            'CS-A', 'CS-B',
            'EC-A', 'EC-B', 'EC-C',
            'EE-A', 'EE-B', 'EE-C',
            'IT-A', 'IT-B',
            'ME-A', 'ME-B', 'ME-C',
            'PI-A', 'PI-B'
        )

    def generateotp(self):
        sample_set = '01234567890123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        OTP = ''
        for i in range(5):
            OTP += sample_set[math.floor(random.random() * 46)]
        return OTP

    @commands.group(brief='Registers the user in the database')
    async def verify(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.reply(l10n.format_value('verify-invalid-command'))
            return

        self.c.execute('SELECT Verified from main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        details = self.c.fetchone()
        if details:
            if details[0] == 'False':
                if ctx.invoked_subcommand.name == 'basic':
                    raise commands.CheckFailure('AccountAlreadyLinked')
            else:
                raise commands.CheckFailure('UserAlreadyVerified')

    @verify.command(brief='Allows user to link their account to a record in the database')
    async def basic(self, ctx, section: str, roll_no: int):
        # Gets the record of the given roll number
        self.c.execute('SELECT Section, Subsection, Name, Discord_UID, Guilds from main where Roll_Number = (:roll)', {'roll': roll_no})
        tuple = self.c.fetchone()
        # Exit if roll number doesn't exist
        if not tuple:
            await ctx.reply(l10n.format_value('verify-basic-record-notfound'))
            return
        # Exit if entered section doesn't match an existing section
        if section not in self.sections:
            await ctx.reply(l10n.format_value('verify-basic-section-notfound', {'section': section}))
            return
        # Exit if entered section doesn't match the section that the roll number is bound to
        if section != tuple[0]:
            await ctx.reply(l10n.format_value('verify-basic-section-mismatch'))
            return
        # Exit if the record is already claimed by another user
        if user := self.bot.get_user(tuple[3]):
            await ctx.reply(l10n.format_value('verify-basic-already-claimed', {'user': f'{user}'}))
            return
        # Assigning one SubSection and one Section role to the user
        role = utils.get(ctx.guild.roles, name=tuple[0])
        await ctx.author.add_roles(role)
        role = utils.get(ctx.guild.roles, name=tuple[1])
        await ctx.author.add_roles(role)
        await ctx.reply(l10n.format_value('verify-basic-success'))
        role = utils.get(ctx.guild.roles, name = 'Not-Verified')
        await ctx.author.remove_roles(role)
        # Fetches the mutual guilds list from the user
        guilds = json.loads(tuple[4])
        # Adds the new guild id if it is a new one
        if ctx.guild.id not in guilds:
            guilds.append(ctx.guild.id)
        guilds = json.dumps(guilds)
        # Updating the record in the database
        self.c.execute('UPDATE main SET Discord_UID = (:uid), Guilds = (:guilds) WHERE Roll_Number = (:roll)', {'uid': ctx.author.id, 'roll': roll_no, 'guilds': guilds})
        self.conn.commit()

        first_name = tuple[2].split(' ', 1)[0].capitalize()
        await ctx.author.edit(nick=first_name)

    @verify.command(brief='Allows user to verify their email')
    @commands.check(basicVerificationCheck)
    async def email(self, ctx, email: str):
        self.c.execute('SELECT Name, Institute_Email from main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        tuple = self.c.fetchone()

        if email.lower() != tuple[1]:
            await ctx.reply(l10n.format_value('verify-email-mismatch'))
            return

        await ctx.message.add_reaction(self.emojis['loading'])

        # Setting variables for the email
        EMAIL = os.getenv('EMAIL')
        PASSWORD = os.getenv('PASSWORD')
        name = tuple[0].title().strip()
        otp = self.generateotp()

        # Creating the email
        msg = EmailMessage()
        msg['Subject'] = f'Verification of {ctx.author} on {ctx.guild}'
        msg['From'] = EMAIL
        msg['To'] = tuple[1]
        msg.set_content(
            l10n.format_value('verify-email-HTML', {'user': name, 'otp': otp, 'guild': ctx.guild.name, 'prefix': ctx.prefix}),
            subtype='html'
        )

        # Sending the email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL, PASSWORD)
            smtp.send_message(msg)

        await ctx.reply(l10n.format_value('verify-check-email', { 'prefix': ctx.prefix }))
        await ctx.message.remove_reaction(self.emojis['loading'], self.bot.user)

        self.data[str(ctx.author.id)] = otp
        self.save()

    @verify.command(brief='Used to input OTP that the user received in order to verify their email')
    @commands.check(basicVerificationCheck)
    async def code(self, ctx, code: str):
        if str(ctx.author.id) not in self.data:
            await ctx.reply(l10n.format_value('verify-not-received'))
            return

        if self.data[str(ctx.author.id)] == code:
            # Deletes the code
            del self.data[str(ctx.author.id)]
            self.save()

            # Marks user as verified in the database
            self.c.execute('UPDATE main SET Verified = "True" where Discord_UID = (:uid)', {'uid': ctx.author.id})
            self.conn.commit()

            await ctx.reply(l10n.format_value('verify-email-success', {'emoji': self.emojis['verified']}))
        else:
            await ctx.reply(l10n.format_value('verify-code-incorrect'))

    def save(self):
        with open('db/codes.json', 'w') as f:
            json.dump(self.data, f)

def setup(bot):
    bot.add_cog(Verify(bot))
