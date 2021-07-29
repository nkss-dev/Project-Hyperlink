import discord, sqlite3, json, pytz
from discord.ext import commands, tasks
from discord.utils import get, sleep_until
from datetime import datetime, timedelta

class Links(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

        try:
            with open('db/links.json', 'r') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {}

        self.days = ('Monday', 'Tuesday', 'Wednesday', 'Thrusday', 'Friday', 'Saturday', 'Sunday')
        self.time = ('8:30', '9:25', '10:40', '11:35', '12:30', '1:45', '2:40', '3:35', '4:30', '5:00')

        self.link_update_loop.start()

    async def cog_check(self, ctx):
        self.c.execute('SELECT Verified, Section, Batch FROM main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        tuple = self.c.fetchone()
        if not tuple:
            raise Exception('AccountNotLinked')
        if tuple[0] == 'False':
            raise Exception('EmailNotVerified')

        flag = False
        manager_roles = [ctx.guild.get_role(role) for role in self.data[str(tuple[2])]['manager_roles']]
        for manager_role in manager_roles:
            if manager_role in ctx.author.roles:
                flag = True
                break
        if not flag:
            await ctx.reply('You\'re not authorised to use this command.')
            return False
        else:
            channel = self.bot.get_channel(self.data[str(tuple[2])][tuple[1]]['channel'])
            if ctx.channel.id != channel.id:
                await ctx.reply(f'To prevent section specific links from being accessible to everyone, this command can only be run in specified channels ({channel.mention} in your case).')
                return False
            return True

    async def create(self, tuple):
        guild = self.bot.get_guild(self.data[str(tuple[1])]['server_ID'][0])

        datetime_ist = datetime.now(pytz.timezone('Asia/Kolkata')) + timedelta(hours=4)
        date = datetime_ist.strftime('%d-%m-%Y')
        day = datetime_ist.strftime('%A')
        timetable = self.data[str(tuple[1])][tuple[0]][day]
        description = f'**Upcoming Classes:**\n({date})\n\n'
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
                    link += 'Link unavailable'
                description += f'\n{subject} ({time}):\n{link}\n'

        if not flag:
            description += 'No class times inputted'

        return description

    async def edit(self, embed: discord.Message, description):
        new_embed = discord.Embed(
            description = description,
            color = discord.Color.blurple()
        )
        await embed.edit(embed=new_embed)

    @commands.group(name='link', brief='Allows certain members to add links to section specific dashboard')
    async def link(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.reply('Invalid link command passed.')
            return

    @link.command(name='create', brief='Creates the dashboard embed')
    async def init(self, ctx):
        self.c.execute('SELECT Section, Batch FROM main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        tuple = self.c.fetchone()

        embed = discord.Embed(
            description = await self.create(tuple),
            color = discord.Color.blurple()
        )

        self.data[str(tuple[1])][tuple[0]]['message'] = (await ctx.send(embed=embed)).id
        self.save()

    @link.command(name='add', brief='Used to add temporary links')
    async def add(self, ctx, time, subject, *, link='Link unavailable'):
        self.c.execute('SELECT Section, Batch FROM main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        tuple = self.c.fetchone()

        message = await ctx.fetch_message(self.data[str(tuple[1])][tuple[0]]['message'])
        description = message.embeds[0].description
        if f'{subject} ({time}):' in description:
            old_link = description.split(f'{subject} ({time}):\n', 1)[1].split('\n', 1)[0]
            old = f'{subject} ({time}):\n{old_link}'
            if 'only:' in old_link:
                new = f"{subject} ({time}):\n{old_link.split(': ')[0]}: {link}"
            else:
                new = f'{subject} ({time}):\n{link}'
            description = description.replace(old, new)
        else:
            times = [class_time.split(')')[0] for class_time in description.split('(')[2:]]
            subjects = [lecture.split(' (')[0] for lecture in description.split('\n')[2:] if '(' in lecture]
            for lecture, class_time in zip(subjects, times):
                if datetime.strptime(time, '%I:%M%p') <= datetime.strptime(class_time, '%I:%M%p'):
                    description = description.replace(f'{lecture} ({class_time})', f'{subject} ({time}):\n{link}\n\n{lecture} ({class_time})')
                    break
        await self.edit(message, description)

    @link.command(name='remove', brief='Used to remove temporary links')
    async def remove(self, ctx, time, subject):
        self.c.execute('SELECT Section, Batch FROM main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        tuple = self.c.fetchone()

        message = await ctx.fetch_message(self.data[str(tuple[1])][tuple[0]]['message'])
        description = message.embeds[0].description
        if f'{subject} ({time}):' in description:
            desc = description.split(f'\n\n{subject} ({time}):\n')
            try:
                remainder = desc[1].split('\n', 1)[1]
            except:
                remainder = ''
            desc = f'{desc[0]}\n{remainder}'
            await self.edit(message, desc)

    @link.command(name='set_default', brief='Used to create a class time', aliases=['sd'])
    async def setd(self, ctx, name, time, link='Link unavailable'):
        pass

    @link.command(name='remove_default', brief='Used to remove a class time', aliases=['rd'])
    async def remd(self, ctx, time):
        pass

    @link.command(name='perm_link_add', brief='Used to add permanent links', aliases=['pla'])
    async def perm_link_add(self, ctx, link, subject, subsection=None):
        pass

    @link.command(name='perm_link_remove', brief='Used to remove permanent links', aliases=['plr'])
    async def perm_link_remove(self, ctx, subject, subsection=None):
        pass

    @tasks.loop(hours=24)
    async def link_update_loop(self):
        while True:
            try:
                with open('db/links.json') as f:
                    data = json.load(f)
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
                    except:
                        pass

    @link_update_loop.before_loop
    async def wait_until_12am(self):
        IST = pytz.timezone('Asia/Kolkata')
        now = datetime.now(IST)
        next_run = now.replace(hour=20, minute=0, second=0)
        if next_run < now:
            next_run += timedelta(days=1)
        await sleep_until(next_run)

    def save(self):
        with open('db/links.json', 'w') as f:
            json.dump(self.data, f)

def setup(bot):
    bot.add_cog(Links(bot))
