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

        ids = await self.bot.conn.fetch('''
            SELECT
                id
            FROM
                verified_server
            UNION
            SELECT
                id AS group_id
            FROM
                group_discord
            WHERE
                group_discord IS NOT NULL
        ''')
        self.server_ids = {'verified': [], 'groups': []}
        for id in ids:
            if id := id.get('id'):
                self.server_ids['verified'].append(id)
            elif id := id.get('group_id'):
                self.server_ids['groups'].append(id)

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

    async def validate_otp(self, user_id: int, code: str) -> bool:
        """Check if the entered code matches the OTP"""
        if self.codes[str(user_id)] != code:
            return False

        del self.codes[str(user_id)]
        self.save()

        # Marks user as verified in the database
        await self.bot.conn.execute(
            'UPDATE student SET verified = true WHERE discord_uid = $1',
            user_id
        )
        return True

    @commands.group()
    @commands.guild_only()
    async def verify(self, ctx):
        """Command group for verification functionality"""
        if not ctx.invoked_subcommand:
            await ctx.send_help(ctx.command)
            return

        l10n = get_l10n(ctx.guild.id, 'verification')
        self.fmv = l10n.format_value

        verified = await self.bot.conn.fetch(
            'SELECT verified FROM student WHERE discord_uid = $1',
            ctx.author.id
        )

        if verified:
            if verified[0]['verified'] is False:
                if ctx.invoked_subcommand.name == 'basic':
                    raise commands.CheckFailure('AccountAlreadyLinked')
            else:
                raise commands.CheckFailure('UserAlreadyVerified')

    async def cleanup(self, author, name):
        """Execute finisher code after successful verification"""
        guild = author.guild

        # Remove restricting role
        id = await self.bot.conn.fetchval(
            'SELECT guest_role FROM verified_server WHERE id = $1', guild.id
        )
        if guest_role := guild.get_role(id):
            await author.remove_roles(guest_role)

        # Add nickname
        if author.display_name != name:
            first_name = name.split(' ', 1)[0]
            await author.edit(nick=first_name)

    async def kick_from_all(self, user_id: int, new_user: str):
        """Kick the user from all affiliated servers"""
        ids = *self.server_ids['verified'], *self.server_ids['groups']
        for id in ids:
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

        record = await self.bot.conn.fetchrow(
            '''
            SELECT
                section,
                sub_section,
                name,
                email,
                batch,
                hostel_number,
                discord_uid
            FROM
                student
            WHERE
                roll_number = $1
            ''', roll_no
        )

        if not record:
            await ctx.reply(self.fmv('roll-not-in-database'))
            return

        guild = ctx.guild
        batch = await self.bot.conn.fetchval(
            'SELECT batch FROM verified_server WHERE id = $1', guild.id
        )
        # Check if server exists
        if batch is not None:
            # Check if the server is year-specific and it matches the student's batch
            if batch != 0 and record['batch'] != batch:
                await ctx.reply(
                    self.fmv('incorrect-server', {'batch': record['batch']})
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

        if section not in self.sections[record['batch']]:
            await ctx.reply(self.fmv('section-notfound', {'section': section}))
            return

        if section != record['section']:
            await ctx.reply(
                self.fmv('section-mismatch'))
            return

        if record['discord_uid']:
            if not (user := guild.get_member(record['discord_uid'])):
                user = self.bot.get_user(record['discord_uid'])
            values = {'email': record['email']}
            if user:
                values['another user'] = user.mention

            await self.sendEmail(
                ctx,
                record['name'],
                record['email'],
                manual=False
            )
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
                    if not await self.validate_otp(ctx.author.id, content):
                        await ctx.reply(
                            self.fmv('code-retry', {'code': content})
                        )
                        continue
                    self.bot.conn.execute(
                        '''
                        UPDATE
                            student
                        SET
                            verified = true
                        WHERE
                            roll_number = $1
                        ''', roll_no
                    )

                    # Fetch the user ID again in case another
                    # account has verified in the meantime
                    user_id = await self.bot.conn.fetchval(
                        'SELECT discord_uid FROM student WHERE roll_number = $1',
                        roll_no
                    )
                    # Kick the old account if any
                    await self.kick_from_all(user_id, ctx.author.mention)
                    break

        await assign_student_roles(
            ctx.author,
            (
                record['section'][:2],
                record['section'],
                record['sub_section'],
                record['batch'],
                record['hostel_number']
            ),
            self.bot.conn
        )

        await ctx.reply(self.fmv('basic-success'))

        await self.bot.conn.execute(
            'UPDATE student SET discord_uid = $1 WHERE roll_number = $2',
            ctx.author.id, roll_no
        )

        await self.cleanup(ctx.author, record['name'])

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
        name, institute_email = await self.bot.conn.fetchrow(
            'SELECT name, email FROM student WHERE discord_uid = $1',
            ctx.author.id
        )

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

        if await self.validate_otp(ctx.author.id, code):
            details = await self.bot.conn.fetchval(
                '''
                SELECT
                    section,
                    sub_section,
                    name,
                    batch,
                    hostel_number
                FROM
                    student
                WHERE
                    discord_uid = $1
                ''', ctx.author.id
            )
            await assign_student_roles(
                ctx.author,
                (
                    details['section'][:2],
                    details['section'],
                    details['sub_section'],
                    details['batch'],
                    details['hostel_number'],
                ),
                self.bot.conn
            )
            await self.cleanup(ctx.author, details['name'])

            await ctx.reply(self.fmv(
                    'email-success', {'emoji': self.emojis['verified']}))
        else:
            await ctx.reply(self.fmv('code-incorrect'))

    def save(self):
        """Save the data to a json file"""
        with open('db/codes.json', 'w') as f:
            json.dump(self.codes, f)


async def setup(bot):
    await bot.add_cog(Verify(bot))
