import json
import sqlite3
from utils.l10n import get_l10n

from datetime import datetime, timedelta
from pytz import timezone

import discord
from discord.ext import commands, tasks
from discord.utils import get, sleep_until

class Links(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open('db/links.json', 'r') as f:
            self.data = json.load(f)

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

        self.days = ('Monday', 'Tuesday', 'Wednesday', 'Thrusday', 'Friday', 'Saturday', 'Sunday')
        self.time = ('8:30', '9:25', '10:40', '11:35', '12:30', '1:45', '2:40', '3:35', '4:30', '5:00')

        self.link_update_loop.start()

    async def cog_check(self, ctx):
        if not self.bot.verificationCheck(ctx):
            return False

        self.l10n = get_l10n(ctx.guild.id, 'links')

        self.tuple = self.c.execute(
            'select Section, Batch from main where Discord_UID = (:uid)',
            {'uid': ctx.author.id}
        ).fetchone()

        await commands.has_any_role(*self.data[str(self.tuple[1])]['manager_roles']).predicate(ctx)

        channel = self.bot.get_channel(self.data[str(self.tuple[1])][self.tuple[0]]['channel'])
        if channel != ctx.channel:
            await ctx.reply(self.l10n.format_value('link-protection', {'channel': channel.mention}))
            return False
        return True

    async def create(self, tuple):
        guild = self.bot.get_guild(self.data[str(tuple[1])]['server_ID'][0])
        self.l10n = get_l10n(guild.id, 'links')

        datetime_ist = datetime.now(timezone('Asia/Kolkata')) + timedelta(hours=7)
        date = datetime_ist.strftime('%d-%m-%Y')
        day = datetime_ist.strftime('%A')
        timetable = self.data[str(tuple[1])][tuple[0]][day]
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

    async def edit(self, embed: discord.Message, description):
        new_embed = discord.Embed(
            description = description,
            color = discord.Color.blurple()
        )
        await embed.edit(embed=new_embed)

    @commands.group(brief='Allows certain members to add links to section specific dashboard')
    async def link(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.reply(self.l10n.format_value('invalid-command', {'name': ctx.command.name}))
            return

    @link.command(name='create', brief='Creates the dashboard embed')
    async def init(self, ctx):
        embed = discord.Embed(
            description = await self.create(self.tuple),
            color = discord.Color.blurple()
        )

        try:
            old_message = await ctx.channel.fetch_message(self.data[str(self.tuple[1])][self.tuple[0]]['message'])
            await old_message.delete()
        except discord.NotFound:
            pass

        self.data[str(self.tuple[1])][self.tuple[0]]['message'] = (await ctx.send(embed=embed)).id
        self.save()

        await ctx.message.delete()

    @link.command(brief='Used to add temporary links')
    async def add(self, ctx, time, subject, *, link='Link unavailable'):
        message = await ctx.fetch_message(self.data[str(self.tuple[1])][self.tuple[0]]['message'])
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
        await ctx.message.delete()

    @link.command(brief='Used to remove temporary links')
    async def remove(self, ctx, time, subject):
        message = await ctx.fetch_message(self.data[str(self.tuple[1])][self.tuple[0]]['message'])
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

    @link.command(name='set_default', brief='Used to create a class time', aliases=['sd'])
    async def setd(self, ctx, name, time, link='Link unavailable'):
        pass

    @link.command(name='remove_default', brief='Used to remove a class time', aliases=['rd'])
    async def remd(self, ctx, time):
        pass

    @link.command(name='perm_link_add', brief='Used to add permanent links', aliases=['pla'])
    async def pla(self, ctx, link, subject, subsection=None):
        pass

    @link.command(name='perm_link_remove', brief='Used to remove permanent links', aliases=['plr'])
    async def plr(self, ctx, subject, subsection=None):
        pass

    @tasks.loop(hours=24)
    async def link_update_loop(self):
        while True:
            try:
                with open('db/links.json') as f:
                    self.data = json.load(f)
                break
            except FileNotFoundError:
                continue
        for batch in self.data:
            for section in self.data[batch]:
                if isinstance(self.data[batch][section], list):
                    continue
                channel = self.bot.get_channel(self.data[batch][section]['channel'])
                if channel:
                    try:
                        message = await channel.fetch_message(self.data[batch][section]['message'])
                        await self.edit(message, await self.create((section, batch)))
                    except discord.NotFound:
                        pass

    @link_update_loop.before_loop
    async def wait_until_12am(self):
        IST = timezone('Asia/Kolkata')
        now = datetime.now(IST)
        next_run = now.replace(hour=17, minute=0, second=0)
        if next_run < now:
            next_run += timedelta(days=1)
        await sleep_until(next_run)

    def save(self):
        with open('db/links.json', 'w') as f:
            json.dump(self.data, f)

def setup(bot):
    bot.add_cog(Links(bot))
