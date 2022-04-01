import contextlib
import json
import re
from asyncio import TimeoutError
from dataclasses import dataclass
from typing import Optional

import config
import discord
from discord.ext import commands
import smtplib
from email.message import EmailMessage

from utils import checks
from utils.l10n import get_l10n
from utils.utils import assign_student_roles, generateID


@dataclass
class BasicInfo:
    branch: Optional[str]
    section: Optional[str]
    roll: Optional[int]


def parse_verify_basic(params: str) -> BasicInfo:
    roll = None
    branch = None
    section = None

    if roll_no := re.search(r'\d{4,}', params):
        roll = int(roll_no.group(0))

    # try XY-A or XY-A2
    if section_name := re.search(r'([A-Z]{2})[- ]?([ABC])?', params, re.I):
        branch = section_name.group(1)
        section = section_name.group(2)

    return BasicInfo(branch, section, roll)


class Verify(commands.Cog):
    """Verification management"""

    def __init__(self, bot):
        self.bot = bot

        with open('db/codes.json') as codes:
            self.codes = json.load(codes)
        with open('db/emojis.json') as emojis:
            self.emojis = json.load(emojis)['utility']

    async def cog_load(self):
        sections = await self.bot.conn.fetch('''
            SELECT
                batch,
                ARRAY_AGG(DISTINCT section)
            FROM
                student
            GROUP BY
                batch
        ''')
        self.sections = dict(sections)

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
            '{$user}'   : name,
            '{$otp}'    : otp,
            '{$guild}'  : ctx.guild.name,
            '{$channel}': 'https://discord.com/channels/'
            + f'{ctx.guild.id}/{ctx.channel.id}',
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

        await ctx.message.remove_reaction(
            self.emojis['loading'], self.bot.user)

        self.codes[str(ctx.author.id)] = otp
        self.save()

    def checkCode(self, author_id: int, code: str) -> bool:
        """Check if the entered code matches the OTP"""
        if self.codes[str(author_id)] != code:
            return False

        del self.codes[str(author_id)]
        self.save()

        # Marks user as verified in the database
        self.bot.c.execute(
            'update main set Verified = 1 where Discord_UID = ?',
            (author_id,)
        )
        self.bot.db.commit()
        return True

    @commands.group()
    @commands.guild_only()
    async def verify(self, ctx):
        """Command group for verification functionality"""
        l10n = get_l10n(ctx.guild.id, 'verification')
        self.fmv = l10n.format_value

        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)
            return

        verified = self.bot.c.execute(
            'select Verified from main where Discord_UID = ?', (ctx.author.id,)
        ).fetchall()

        if verified:
            if not verified[0]:
                if ctx.invoked_subcommand.name == 'basic':
                    raise commands.CheckFailure('AccountAlreadyLinked')
            else:
                raise commands.CheckFailure('UserAlreadyVerified')

    async def cleanup(self, author, name):
        """Execute finisher code after successful verification"""
        guild = author.guild

        # Remove restricting role
        id = self.bot.c.execute(
            'select Guest_Role from verified_servers where ID = ?', (guild.id,)
        ).fetchone()
        if guest_role := guild.get_role(id):
            await author.remove_roles(guest_role)

        # Add nickname
        if author.display_name != name:
            first_name = name.split(' ', 1)[0]
            await author.edit(nick=first_name)

    async def kick_from_all(self, user_id: int):
        """Kick the user from all affiliated servers"""
        server_ids = self.bot.c.execute(
            'select ID from verified_servers'
            + ' union '
            + 'select Discord_Server from groups'
        ).fetchall()
        for id in server_ids:
            guild = self.bot.get_guild(id)
            if guild and (member := guild.get_member(user_id)):
                with contextlib.suppress(discord.Forbidden):
                    await member.kick(
                        reason=self.fmv('member-kick', {'user': new_user})
                    )

    @verify.command()
    async def basic(self, ctx, *, params: str):
        """Type this command to gain access to servers and much more.

        Type `verify basic` followed by your branch and section, like \
        `CS-A`, followed by your roll number.

        Example: `%verify basic CS-B 12022005`
        """
        """
        Parameters
        ------------
        `section`: <class 'str'>
            The section the student is in. Must match the following format:
                XY-Z
            where `XY` is the acronym for the branch and `Z` is the section.

        `roll_no`: <class 'int'>
            The roll number of the student.
        """
        if str(ctx.author.id) in self.codes:
            await ctx.reply('pending-verification')
            return

        info = parse_verify_basic(params)

        if info.roll is None:
            await ctx.reply(self.fmv('rollno-not-provided'))
            return

        if info.branch is None:
            await ctx.reply(self.fmv('branch-not-provided'))
            return

        if info.section is None:
            await ctx.reply(self.fmv('section-not-provided'))
            return

        roll_no = info.roll
        section = f'{info.branch}-{info.section}'.upper()

        record = self.bot.c.execute(
            '''select Section, SubSection, Name,
                Institute_Email, Batch, Hostel_Number, Discord_UID
                from main where Roll_Number = ?
            ''', (roll_no,)
        ).fetchone()

        if not record:
            await ctx.reply(self.fmv('roll-not-in-database'))
            return

        guild = ctx.guild
        batch = self.bot.c.execute(
            'select Batch from verified_servers where ID = ?', (guild.id,)
        ).fetchone()
        if batch is not None:
            if batch and record[4] != batch:
                await ctx.reply(
                    self.fmv('incorrect-server', {'batch': record[4]})
                )
                return
        else:
            await ctx.reply(self.fmv('server-not-allowed'))

            def check_owner(msg):
                return msg.author.id in self.bot.owner_ids \
                    and msg.channel == ctx.channel

            try:
                message = await self.bot.wait_for(
                    'message', timeout=60.0, check=check_owner
                )
                if message.content.lower() != 'override':
                    return
            except TimeoutError:
                return

        if section not in self.sections[record[4]]:
            await ctx.reply(self.fmv('section-notfound', {'section': section}))
            return

        if section != record[0]:
            await ctx.reply(
                self.fmv('section-mismatch'))
            return

        if record[6]:
            user = guild.get_member(record[6]) or self.bot.get_user(record[6])
            values = {
                'email': record[3],
                'user': user.mention if user else 'another user'
            }

            await self.sendEmail(ctx, *record[2:4], manual=False)
            await ctx.reply(self.fmv('record-claimed', values))

            def check(msg):
                return msg.author == ctx.author and msg.channel == ctx.channel

            while True:
                try:
                    ctx.message = await self.bot.wait_for(
                        'message', timeout=120.0, check=check
                    )
                except TimeoutError:
                    await ctx.send(self.fmv('react-timeout'))
                    return
                else:
                    content = ctx.message.content
                    if not self.checkCode(ctx.author.id, content):
                        await ctx.reply(
                            self.fmv('code-retry', {'code': content})
                        )
                        continue
                    self.bot.c.execute(
                        'update main set Verified = 1 where Roll_Number = ?',
                        (roll_no,)
                    )

                    # Fetch the user ID again in case another
                    # account has verified in the meantime
                    user_id = self.bot.c.execute(
                        'select Discord_UID from main where Roll_Number = ?',
                        (roll_no,)
                    ).fetchone()

                    # Kick the old account if any
                    await self.kick_from_all(user_id)
                    break

        await assign_student_roles(
            ctx.author, (record[0][:2], *record[:2], *record[4:6]), self.bot.c
        )

        await ctx.reply(self.fmv('basic-success'))

        self.bot.c.execute(
            'update main set Discord_UID = ? where Roll_Number = ?',
            (ctx.author.id, roll_no,)
        )
        self.bot.db.commit()

        await self.cleanup(ctx.author, record[2])

    @verify.command()
    @checks.is_exists()
    async def email(self, ctx, email: str):
        """Type this command to prove your identity for more accessibility.

        Type `verify email` followed by your institute email, like \
        `email@nitkkr.ac.in`

        Example: `%verify email priyanshu_12022005@nitkkr.ac.in`
        """
        """
        Parameters
        ------------
        `email`: <class 'str'>
            The institute email of the user.
        """
        name, institute_email = self.bot.c.execute(
            'select Name, Institute_Email from main where Discord_UID = ?',
            (ctx.author.id,)
        ).fetchone()

        if email.lower() != institute_email:
            await ctx.reply(self.fmv('email-mismatch'))
            return

        await self.sendEmail(ctx, name, institute_email)

        command = ctx.clean_prefix + ctx.command.parent.name
        await ctx.reply(self.fmv('check-email', {'cmd': command}))

    @verify.command()
    @checks.is_exists()
    async def code(self, ctx, code: str):
        """Check if the inputted code matches the sent OTP."""
        """
        Parameters
        ------------
        `code`: <class 'str'>
            The code to be checked
        """
        if str(ctx.author.id) not in self.codes:
            await ctx.reply(self.fmv('email-not-received'))
            return

        if self.checkCode(ctx.author.id, code):
            details = self.bot.c.execute(
                '''select Section, Subsection, Batch, Hostel_Number, Name
                    from main where Discord_UID = ?
                ''', (ctx.author.id,)
            ).fetchone()
            await assign_student_roles(ctx.author, (details[0][:2], *details[:-1]), self.bot.c)
            await self.cleanup(ctx.author, details[-1])

            await ctx.reply(self.fmv(
                    'email-success', {'emoji': self.emojis['verified']}))
        else:
            await ctx.reply(self.fmv('code-incorrect'))

    def save(self):
        """Save the data to a json file"""
        with open('db/codes.json', 'w') as f:
            json.dump(self.codes, f)


def setup(bot):
    bot.add_cog(Verify(bot))