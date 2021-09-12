import json
import sqlite3
from utils.l10n import get_l10n

from datetime import datetime, timedelta
from pytz import timezone

import discord
from discord.ext import commands, tasks
from discord.utils import get, sleep_until

class Links(commands.Cog):
    """Dashboard setup for class links"""

    def __init__(self, bot):
        self.bot = bot

        with open('db/links.json') as f:
            self.links = json.load(f)

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

        self.days = ('Monday', 'Tuesday', 'Wednesday', 'Thrusday', 'Friday', 'Saturday', 'Sunday')
        self.time = ('8:30', '9:25', '10:40', '11:35', '12:30', '1:45', '2:40', '3:35', '4:30', '5:00')

        self.linkUpdateLoop.start()

    async def cog_check(self, ctx) -> bool:
        if not ctx.guild:
            raise commands.NoPrivateMessage
        if not self.bot.verificationCheck(ctx):
            return False

        self.tuple = self.c.execute(
            'select Section, Batch from main where Discord_UID = (:uid)',
            {'uid': ctx.author.id}
        ).fetchone()

        manager_roles = self.links[str(self.tuple[1])]['manager_roles']
        await commands.has_any_role(*manager_roles).predicate(ctx)

        channel = self.bot.get_channel(self.links[str(self.tuple[1])][self.tuple[0]]['channel'])
        if channel != ctx.channel:
            raise commands.CheckFailure('LinkProtection')

        self.l10n = get_l10n(ctx.guild.id, 'links')
        return True

    async def create(self, tuple: tuple[str, str]) -> str:
        """return links for the given section"""
        guild = self.bot.get_guild(self.links[str(tuple[1])]['server_ID'][0])
        self.l10n = get_l10n(guild.id, 'links')

        datetime_ist = datetime.now(timezone('Asia/Kolkata')) + timedelta(hours=7)
        date = datetime_ist.strftime('%d-%m-%Y')
        day = datetime_ist.strftime('%A')
        timetable = self.links[str(tuple[1])][tuple[0]][day]
        description = self.l10n.format_value('link-embed-title', {'date': date})

        flag = False
        for lecture in timetable:
            time = lecture['time']
            subject = lecture['subject']
            link = lecture['link']
            if subject:
                flag = True
                temp = []
                for i in range(len(link)):
                    if link[i] == '@' and link[i+1] != '&':
                        temp.append([link[i:i+6], get(guild.roles, name=link[i+1:i+6]).mention])

                for role in temp:
                    link = link.replace(role[0], role[1])
                if 'http' not in link:
                    link += self.l10n.format_value('link-notfound')
                description += f'\n{subject} ({time}):\n{link}\n'

        if not flag:
            description += self.l10n.format_value('links-notfound')

        return description

    async def edit(self, message: discord.Message, description: str):
        """edit the given message with a refreshed description"""
        new_embed = discord.Embed(
            description = description,
            color = discord.Color.blurple()
        )
        await message.edit(embed=new_embed)

    @commands.group()
    async def link(self, ctx):
        """Command group for links dashboard functionality"""
        if not ctx.invoked_subcommand:
            await ctx.reply(self.l10n.format_value('invalid-command', {'name': ctx.command.name}))
            return

    @link.command(name='create')
    async def init(self, ctx):
        """Send the links embed to a dashboard"""
        embed = discord.Embed(
            description = await self.create(self.tuple),
            color = discord.Color.blurple()
        )

        # Delete an older embed if any
        try:
            message_id = self.links[str(self.tuple[1])][self.tuple[0]]['message']
            old_message = await ctx.channel.fetch_message(message_id)
            await old_message.delete()
        except discord.NotFound:
            pass

        self.links[str(self.tuple[1])][self.tuple[0]]['message'] = (await ctx.send(embed=embed)).id
        self.save()

        if ctx.guild.me.guild_permissions.manage_messages:
            await ctx.message.delete()

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
        message = await ctx.fetch_message(self.links[str(self.tuple[1])][self.tuple[0]]['message'])
        description = message.embeds[0].description

        if f'{subject} ({time}):' in description:
            old_link = description.split(f'{subject} ({time}):\n', 1)[1].split('\n', 1)[0]
            old = f'{subject} ({time}):\n{old_link}'

            if self.l10n.format_value('section-check') in old_link:
                new = f"{subject} ({time}):\n{old_link.split(': ')[0]}: {link}"
            else:
                new = f'{subject} ({time}):\n{link}'

            description = description.replace(old, new)
        else:
            times = [class_time.split(')')[0] for class_time in description.split('(')[2:]]
            subjects = [lecture.split(' (')[0] for lecture in description.split('\n')[2:] if '(' in lecture]

            flag = False
            for lecture, class_time in zip(subjects, times):
                if datetime.strptime(time, '%I:%M%p') < datetime.strptime(class_time, '%I:%M%p'):
                    description = description.replace(f'{lecture} ({class_time})', f'{subject} ({time}):\n{link}\n\n{lecture} ({class_time})')
                    flag = True
                    break

            if not flag:
                description = description.replace(self.l10n.format_value('links-notfound'), '')
                description += f'{subject} ({time}):\n{link}'

        await self.edit(message, description)
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
        message = await ctx.fetch_message(self.links[str(self.tuple[1])][self.tuple[0]]['message'])
        description = message.embeds[0].description

        if f'{subject} ({time}):' in description:
            desc = description.split(f'\n\n{subject} ({time}):\n', 1)
            try:
                remainder = desc[1].split('\n', 1)[1]
            except IndexError:
                remainder = f"\n{self.l10n.format_value('links-notfound')}"

            desc = f'{desc[0]}\n{remainder}'

            await self.edit(message, desc)
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
        """update links in all embeds every 24 hours"""
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
                        await self.edit(message, await self.create((section, batch)))
                    except discord.NotFound:
                        pass

    @linkUpdateLoop.before_loop
    async def delay(self):
        """add delay before running daily loop"""
        IST = timezone('Asia/Kolkata')
        now = datetime.now(IST)
        next_run = now.replace(hour=17, minute=0, second=0)
        if next_run < now:
            next_run += timedelta(days=1)
        await sleep_until(next_run)

    def save(self):
        """save the data to a json file"""
        with open('db/links.json', 'w') as f:
            json.dump(self.links, f)

def setup(bot):
    """invoked when this file is attempted to be loaded as an extension"""
    bot.add_cog(Links(bot))
