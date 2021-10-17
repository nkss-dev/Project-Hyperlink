import json
import re
from utils.l10n import get_l10n
from utils.utils import getURLs

from datetime import datetime, timedelta
from pytz import timezone

import discord
from discord.ext import commands, tasks
from discord.utils import get, sleep_until

class Links(commands.Cog):
    """Dashboard setup for class links"""

    def __init__(self, bot):
        self.bot = bot
        self.section = ''
        self.batch = ''

        with open('db/links.json') as f:
            self.links = json.load(f)

        self.days = ('Monday', 'Tuesday', 'Wednesday', 'Thrusday', 'Friday', 'Saturday', 'Sunday')
        self.time = ('8:30', '9:25', '10:40', '11:35', '12:30', '1:45', '2:40', '3:35', '4:30', '5:00')

        self.linkUpdateLoop.start()

    async def cog_check(self, ctx) -> bool:
        if not ctx.guild:
            raise commands.NoPrivateMessage
        if not self.bot.verificationCheck(ctx):
            return False

        self.section, self.batch = self.bot.c.execute(
            'select Section, Batch from main where Discord_UID = (:uid)',
            {'uid': ctx.author.id}
        ).fetchone()
        self.batch = str(self.batch)

        manager_roles = self.links[self.batch]['manager_roles']
        await commands.has_any_role(*manager_roles).predicate(ctx)

        channel = self.bot.get_channel(self.links[self.batch][self.section]['channel'])
        if channel != ctx.channel and ctx.author != ctx.guild.owner:
            raise commands.CheckFailure('LinkProtection')

        self.l10n = get_l10n(ctx.guild.id, 'links')
        return True

    @staticmethod
    def replace_role_tags(roles: list[discord.Role], string: str) -> str:
        if role_IDs := re.findall('@[CEIMP][CEIST]-0[1-9]', string, flags=re.I):
            for role_ID in role_IDs:
                try:
                    role = get(roles, name=role_ID[1:].upper())
                    string = string.replace(role_ID, role.mention, 1)
                except AttributeError:
                    continue
        return string

    def create(self, section: str, batch: str) -> discord.Embed:
        """Return links for the given section"""
        guild = self.bot.get_guild(self.links[batch]['server_ID'][0])
        self.l10n = get_l10n(guild.id, 'links')

        time = datetime.now(timezone('Asia/Kolkata')) + timedelta(hours=7)
        date = time.strftime('%d-%m-%Y')
        day = time.strftime('%A')
        timetable = self.links[batch][section][day]
        times = [date]

        for lecture in timetable:
            link = self.replace_role_tags(guild.roles, lecture['link'])

            if not getURLs(link):
                link += self.l10n.format_value('link-notfound')

            times.append((f"{lecture['subject']} ({lecture['time']}):", link))

        embed = discord.Embed(
            title=self.l10n.format_value('link-embed-title'),
            description=times[0],
            color=discord.Color.blurple()
        )
        if len(times) == 1:
            embed.set_footer(text=self.l10n.format_value('links-notfound'))
        else:
            for time, link in times[1:]:
                embed.add_field(name=time, value=link, inline=False)

        return embed

    @commands.group(invoke_without_command=True)
    async def link(self, ctx):
        """Command group for links dashboard functionality"""
        await ctx.send_help(ctx.command)

    @link.group(aliases=['r'], invoke_without_command=True)
    async def refresh(self, ctx):
        """Refresh an existing link embed in a dashboard.

        If an embed does not exist, a new one is created.
        """
        try:
            message_id = self.links[self.batch][self.section]['message']
            message = await ctx.channel.fetch_message(message_id)
        except discord.NotFound:
            message = await ctx.channel.send('\u200b')
            self.links[self.batch][self.section]['message'] = message.id
            self.save()

        await message.edit(embed=self.create(self.section, self.batch))

        if ctx.guild.me.guild_permissions.manage_messages:
            await ctx.message.delete()

    @refresh.command()
    @commands.is_owner()
    async def all(self, ctx):
        """Refresh links in all given channels"""
        await self.linkUpdateLoop()
        await ctx.send(self.l10n.format_value('links-update-success'))

    @link.command()
    async def add(self, ctx, time: str, subject: str, *, link: str='Link unavailable'):
        """Add a link to an existing embed.

        If a class with the same time and subject exists, this command will \
        replace the link for said class. Else, a new schedule will be created.

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
        try:
            time_obj = datetime.strptime(time, '%I:%M%p')
        except ValueError:
            await ctx.send(
                self.l10n.format_value(
                    'invalid-time-format',
                    {'cmd': f'{ctx.clean_prefix}help {ctx.command.qualified_name}'}
                ),
                delete_after=5.0
            )
            return

        try:
            message = await ctx.fetch_message(self.links[self.batch][self.section]['message'])
            embed = message.embeds[0]
        except discord.NotFound:
            await ctx.send(
                self.l10n.format_value(
                    'embed-notfound',
                    {'cmd': f'{ctx.clean_prefix}{ctx.command.parent} create'}
                ),
                delete_after=5.0
            )
            return

        if not embed.fields:
            embed.add_field(
                name=f'{subject} ({time}):',
                value=link,
                inline=False
            )
            embed.remove_footer()

        exists = False
        for i, field in enumerate(embed.fields):
            if field.name == f'{subject} ({time}):':
                exists = True
                if re.search('<@&\d{18}>', field.value):
                    value = f"{field.value.split(':')[0]}: {link}"
                else:
                    value = link
                embed.set_field_at(
                    i,
                    name=field.name,
                    value=value,
                    inline=False
                )
                break

        if not exists:
            times = []
            for i, field in enumerate(embed.fields):
                if match := re.search('\d{1,2}:\d{2}[AP]M', field.name):
                    times.append((i, datetime.strptime(match.group(0), '%I:%M%p')))

            inserted = False
            for i, class_time in times:
                if time_obj < class_time:
                    inserted = True
                    embed.insert_field_at(
                        i,
                        name=f'{subject} ({time}):',
                        value=self.replace_role_tags(message.guild.roles, link)
                    )
                    break

            if not inserted:
                embed.add_field(
                    name=f'{subject} ({time}):',
                    value=self.replace_role_tags(message.guild.roles, link),
                    inline=False
                )

        await message.edit(embed=embed)
        if ctx.guild.me.guild_permissions.manage_messages:
            await ctx.message.delete()

    @link.command()
    async def remove(self, ctx, time: str, subject: str):
        """Remove a link from an existing embed.

        Parameters
        ------------
        `time`: <class 'str'>
            The time at which the class was scheduled. This must match one of \
            the existing times in the embed.

        `subject`: <class 'str'>
            The subject of the class.
        """
        try:
            message = await ctx.fetch_message(self.links[self.batch][self.section]['message'])
            embed = message.embeds[0]
        except discord.NotFound:
            await ctx.send(
                self.l10n.format_value(
                    'embed-notfound',
                    {'cmd': f'{ctx.clean_prefix}{ctx.command.parent} create'}
                ),
                delete_after=5.0
            )
            return

        if not embed.fields:
            await ctx.send(self.l10n.format_value('classes-notfound'), delete_after=5.0)
            return

        exists = False
        for i, field in enumerate(embed.fields):
            if field.name == f'{subject} ({time}):':
                exists = True
                embed.remove_field(i)
                if not embed.fields:
                    embed.set_footer(text=self.l10n.format_value('links-notfound'))

        if not exists:
            await ctx.send(self.l10n.format_value('class-notfound'), delete_after=5.0)
        else:
            await message.edit(embed=embed)

        if ctx.guild.me.guild_permissions.manage_messages:
            await ctx.message.delete()

    @link.command(name='set_default', aliases=['sd'])
    async def setd(self, ctx, name, time, link='Link unavailable'):
        """Unreleased: Used to create a class time"""
        pass

    @link.command(name='remove_default', aliases=['rd'])
    async def remd(self, ctx, time):
        """Unreleased: Used to remove a class time"""
        pass

    @link.command(name='perm_link_add', aliases=['pla'])
    async def pla(self, ctx, link, subject, subsection=None):
        """Unreleased: Used to add permanent links"""
        pass

    @link.command(name='perm_link_remove', aliases=['plr'])
    async def plr(self, ctx, subject, subsection=None):
        """Unreleased: Used to remove permanent links"""
        pass

    @tasks.loop(hours=24)
    async def linkUpdateLoop(self):
        """Update links in all embeds every 24 hours"""
        with open('db/links.json') as f:
            self.links = json.load(f)

        for batch in self.links:
            for section in self.links[batch]:
                if isinstance(self.links[batch][section], list):
                    continue
                channel = self.bot.get_channel(self.links[batch][section]['channel'])
                if channel:
                    try:
                        message = await channel.fetch_message(self.links[batch][section]['message'])
                    except discord.NotFound:
                        message = await channel.send('\u200b')
                        self.links[batch][section]['message'] = message.id
                    await message.edit(embed=self.create(section, batch))
        self.save()

    @linkUpdateLoop.before_loop
    async def delay(self):
        """Add delay before running daily loop"""
        IST = timezone('Asia/Kolkata')
        now = datetime.now(IST)
        next_run = now.replace(hour=17, minute=0, second=0)
        if next_run < now:
            next_run += timedelta(days=1)
        await sleep_until(next_run)

    def save(self):
        """Save the data to a json file"""
        with open('db/links.json', 'w') as f:
            json.dump(self.links, f)

def setup(bot):
    """Called when this file is attempted to be loaded as an extension"""
    bot.add_cog(Links(bot))
