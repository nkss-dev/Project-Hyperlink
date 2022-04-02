import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Iterable, Optional

import discord
from discord.ext import commands, tasks

from utils import checks
from utils.l10n import get_l10n
from utils.utils import getURLs


ROLE_NAME = re.compile('@[CEIMP][CEIST]-[01][0-9]', flags=re.I)
TIME = re.compile(r'\d{1,2}:\d{2}[AP]M', flags=re.I)
FORMAT = '%I:%M%p'


def mention_roles(roles: list[discord.Role], text, pre_mentions, l10n) -> str:
    role_set: set[discord.Role] = set(pre_mentions)
    if text and (role_names := ROLE_NAME.findall(text)):
        for role_name in role_names:
            role = discord.utils.get(roles, name=role_name[1:].upper())
            if role:
                role_set.add(role)

    sorted_roles = sorted(role_set, key=lambda x: x.name)
    mentions = map(lambda x: x.mention, sorted_roles)

    if link := getURLs(text):
        text = link[0]
    else:
        text = l10n.format_value('link-notfound')
    if mentions:
        return f"{' and '.join(mentions)} only: {text}"
    return text


def get_subsecs(text: str, roles: list[discord.Role]) -> Iterable[str]:
    if text and (role_names := ROLE_NAME.findall(text)):
        for role_name in role_names:
            yield role_name[-1]

    for role in roles:
        yield role.name[-1]


def convert_from_24hr(time: str) -> str:
    time = datetime.strptime(time, '%H:%M').strftime(FORMAT)
    return time[1:] if time[0] == '0' else time


def convert_to_24hr(time: str) -> str:
    return datetime.strptime(time, FORMAT).strftime('%H:%M')


@dataclass
class DashboardInfo:
    batch: int
    section: str
    guild_id: int
    channel_id: int
    message_id: int
    roles: Optional[list[int]]


class Links(commands.Cog):
    """Dashboard setup for class links"""

    def __init__(self, bot):
        self.bot = bot
        self.info: DashboardInfo

        self.db = sqlite3.connect('db/links.db')
        self.db.row_factory = lambda _, row: row[0] if len(row) == 1 else row
        self.c = self.db.cursor()

        self.refresh_all_links.start()

    def store_message(self, message: int, channel: int, commit: bool=True):
        self.c.execute(
            'update dashboards set Message = ? where Channel = ?',
            (message, channel)
        )
        if commit:
            self.db.commit()

    def create(self) -> discord.Embed:
        """Return links for the given section"""
        guild_id = self.c.execute(
            'select Guild_ID from link_managers where Batch = ?',
            (self.info.batch,)
        ).fetchone()
        guild = self.bot.get_guild(guild_id)
        self.l10n = get_l10n(guild_id, 'links')

        time = discord.utils.utcnow() + timedelta(hours=12.5)
        date = time.strftime('%d-%m-%Y')
        day = time.strftime('%A')
        timetable = self.c.execute(
            '''select Subject, Time, Link, SubSecs from links
                where Batch = ? and Section = ? and Day = ?
                order by Time
            ''', (self.info.batch, self.info.section, day)
        ).fetchall()

        embed = discord.Embed(
            title=self.l10n.format_value('link-embed-title'),
            description=date,
            color=discord.Color.blurple()
        )

        for subject, time, link, subsecs in timetable:
            roles = []
            if link is None:
                link = ''
            if subsecs:
                for subsec in subsecs.split(','):
                    name = f'{self.info.section[:-1]}0{subsec}'
                    if role := discord.utils.get(guild.roles, name=name):
                        roles.append(role.mention)
            if not getURLs(link):
                link += self.l10n.format_value('link-notfound')

            if roles:
                text = f"{' and '.join(roles)} only: {link}"
            else:
                text = link
            embed.add_field(
                name=f'{subject} ({convert_from_24hr(time)}):',
                value=text,
                inline=False
            )

        if not embed.fields:
            embed.set_footer(text=self.l10n.format_value('links-notfound'))

        return embed

    async def is_time_valid(self, ctx, time: str) -> Optional[datetime]:
        try:
            return datetime.strptime(time, FORMAT)
        except ValueError:
            await ctx.send(
                self.l10n.format_value(
                    'invalid-time-format',
                    {'cmd': self.bot.help(ctx)}
                ), delete_after=15.0
            )
        return

    async def cog_check(self, ctx) -> bool:
        if not ctx.guild:
            raise commands.NoPrivateMessage
        if not await checks.is_verified().predicate(ctx):
            return False

        manager_roles = self.c.execute(
            'select Manager_Role from link_managers where Guild_ID = ?',
            (ctx.guild.id,)
        ).fetchall()
        if manager_roles:
            await commands.has_any_role(*manager_roles).predicate(ctx)
        else:
            return False

        section, batch = self.bot.c.execute(
            'select Section, Batch from main where Discord_UID = ?',
            (ctx.author.id,)
        ).fetchone()

        ids = self.c.execute(
            '''select Channel, Message from dashboards
                where Batch = ? and Section = ?
            ''', (batch, section)
        ).fetchone()
        if ids and ids[0] != ctx.channel.id and ctx.author != ctx.guild.owner:
            raise commands.CheckFailure('LinkProtection')

        self.l10n = get_l10n(ctx.guild.id, 'links')
        self.info = DashboardInfo(
            batch, section, ctx.guild.id, ids[0], ids[1], manager_roles
        )
        return True

    @commands.group(aliases=['l'], invoke_without_command=True)
    async def link(self, ctx):
        """Command group for links dashboard functionality"""
        await ctx.send_help(ctx.command)

    @link.group(aliases=['r'], invoke_without_command=True)
    async def refresh(self, ctx):
        """Refresh an existing link embed in a dashboard.

        If an embed does not exist, a new one is created.
        """
        try:
            message = await ctx.channel.fetch_message(self.info.message_id)
            await message.edit(embed=self.create())
        except discord.HTTPException:
            message = await ctx.channel.send(embed=self.create())
            self.store_message(message.id, ctx.channel.id)

        if ctx.guild.me.guild_permissions.manage_messages:
            await ctx.message.delete()

    @refresh.command()
    @commands.is_owner()
    async def all(self, ctx):
        """Refresh links in all given channels"""
        await self.refresh_all_links()
        await ctx.send(self.l10n.format_value('links-update-success'))

    @link.command()
    async def add(self, ctx, time: str, subject: str, *, link: str='Link unavailable'):
        """Add a link to the dashboard.

        If a class with the same time and subject exists, this command will \
        replace the link for said class. Else, a new class will be created.
        A strict format, `HH:MM(AM/PM)`, is to be followed.
        """
        """
        Parameters
        ------------
        `time`: <class 'str'>
            The time at which the class is scheduled. The link is inserted according \
            to this time. A strict format, `HH:MM(AM/PM)`, is to be followed.
        `subject`: <class 'str'>
            The subject of the class.
        `link`: <class 'str'>
            The link of the class. If left blank, this defaults to `Link unavailable`.
            For classes specific to only one or two sub-sections, please use the \
            following format:
                `@CS-01 only: link`, `@CS-01 and @CS-02 only: link`
            This will convert the section to a role tag for a better viewing experience.
        """
        time_obj = await self.is_time_valid(ctx, time)
        if time_obj is None:
            return

        schedule = {
            'name': f'{subject} ({time}):',
            'value': mention_roles(
                ctx.guild.roles, link, ctx.message.role_mentions, self.l10n
            ),
            'inline': False
        }

        try:
            message = await ctx.fetch_message(self.info.message_id)
            embed = message.embeds[0]
        except discord.NotFound:
            embed = self.create()

        if not embed.fields:
            embed.add_field(**schedule)
            embed.remove_footer()
        else:
            found = False
            for i, field in enumerate(embed.fields):
                if field.name == schedule['name']:
                    found = True
                    if ctx.message.role_mentions:
                        pass
                    elif mentions := re.findall(r'<@&\d{18}>', str(field.value)):
                        roles = []
                        for mention in mentions:
                            roles.append(ctx.guild.get_role(int(mention[3:-1])))
                        schedule['value'] = mention_roles(
                            ctx.guild.roles, link, roles, self.l10n
                        )
                    embed.set_field_at(i, **schedule)
                    break

            if not found:
                inserted = False
                for i, field in enumerate(embed.fields):
                    match = TIME.search(str(field.name))
                    class_time = datetime.strptime(match.group(0), FORMAT)
                    if time_obj < class_time:
                        inserted = True
                        embed.insert_field_at(i, **schedule)
                        break

                if not inserted:
                    embed.add_field(**schedule)

        try:
            await message.edit(embed=embed)
        except NameError:
            message = await ctx.send(embed=embed)
            self.store_message(message.id, ctx.channel.id)

        if ctx.guild.me.guild_permissions.manage_messages:
            await ctx.message.delete()

    @link.command()
    async def remove(self, ctx, time: str, subject: str):
        """Remove a class time from the dashboard."""
        """
        Parameters
        ------------
        `time`: <class 'str'>
            The time at which the class was scheduled. This must match one of \
            the existing times in the embed.
        `subject`: <class 'str'>
            The subject of the class.
        """
        try:
            message = await ctx.fetch_message(self.info.message_id)
            embed = message.embeds[0]
        except discord.NotFound:
            embed = self.create()

        if not embed.fields:
            await ctx.send(
                self.l10n.format_value('classes-notfound'), delete_after=15.0
            )
            return

        found = False
        for i, field in enumerate(embed.fields):
            if field.name == f'{subject} ({time}):':
                found = True
                embed.remove_field(i)
                break
        if found and not embed.fields:
            embed.set_footer(text=self.l10n.format_value('links-notfound'))

        if not found:
            await ctx.send(
                self.l10n.format_value('class-notfound'), delete_after=15.0
            )
        else:
            try:
                await message.edit(embed=embed)
            except NameError:
                message = await ctx.send(embed=embed)
                self.store_message(message.id, ctx.channel.id)

        if ctx.guild.me.guild_permissions.manage_messages:
            await ctx.message.delete()

    @link.command(name='perm_add', aliases=['pa'])
    async def padd(self, ctx, time: str, subject: str, *, link: str=None):
        """Add a permanent schedule to a timetable.

        Creates a new class at the given time. If no link is provided, it is \
        left blank. To remove a link but not a class time, run this command \
        with the respective subject and time without providing the link
        """
        time_obj = await self.is_time_valid(ctx, time)
        if time_obj is None:
            return
        t24 = convert_to_24hr(time)

        if link is not None:
            url = getURLs(link)
            link = url[0] if url else None

        subsecs = ','.join(get_subsecs(link, ctx.message.role_mentions))
        now = discord.utils.utcnow() + timedelta(hours=12.5)
        day = now.strftime('%A')

        try:
            self.c.execute(
                'insert into links values (?,?,?,?,?,?,?)',
                (
                    self.info.batch, self.info.section,
                    day, subject, t24, link, subsecs
                )
            )
        except sqlite3.IntegrityError:
            self.c.execute(
                '''update links set Link = ?, SubSecs = ?
                    where Batch = ? and Section = ? and Day = ?
                    and Subject = ? and Time = ?
                ''',
                (
                    link, subsecs, self.info.batch,
                    self.info.section, day, subject, t24
                )
            )
        self.db.commit()

        await self.add(ctx, time, subject, link=link)

    @link.command(name='perm_remove', aliases=['pr'])
    async def prem(self, ctx, time: str, subject: str):
        """Remove a permanent schedule to a timetable."""
        time_obj = await self.is_time_valid(ctx, time)
        if time_obj is None:
            return
        t24 = convert_to_24hr(time)
        now = discord.utils.utcnow() + timedelta(hours=12.5)
        day = now.strftime('%A')
        self.c.execute(
            '''delete from links where Batch = ? and Section = ?
                and Day = ? and Subject = ? and Time = ?
            ''', (self.info.batch, self.info.section, day, subject, t24)
        )
        self.db.commit()
        await self.remove(ctx, time, subject)

    @tasks.loop(hours=24)
    async def refresh_all_links(self):
        """Update links in all embeds every 24 hours"""
        dashboards = self.c.execute('select * from dashboards').fetchall()
        channels = {id: self.bot.get_channel(id) for *_, id, _ in dashboards}

        for batch, section, channel_id, message_id in dashboards:
            if channel := channels[channel_id]:
                self.info = DashboardInfo(
                    batch, section, channel.guild.id, channel_id, message_id, None
                )
                embed = self.create()
                try:
                    message = await channel.fetch_message(message_id)
                    await message.edit(embed=embed)
                except discord.HTTPException:
                    message = await channel.send(embed=embed)

                    self.store_message(message.id, channel_id, False)
        self.db.commit()

    @refresh_all_links.before_loop
    async def delay(self):
        """Add delay before running daily loop"""
        now = discord.utils.utcnow()
        next_run = now.replace(hour=11, minute=30, second=0)
        if next_run < now:
            next_run += timedelta(days=1)
        await discord.utils.sleep_until(next_run)


async def setup(bot):
    await bot.add_cog(Links(bot))
