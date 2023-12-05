import asyncio
import json
import pytz
from datetime import datetime, timedelta

import discord
from discord.ext import commands

class Reminder(commands.Cog):
    """Bot reminders"""

    def __init__(self, bot):
        self.bot = bot

        with open('db/reminders.json') as f:
            self.data = json.load(f)

        self.bot.loop.create_task(self.reminder_loop())

    @commands.group(name='reminder', brief='Reminds you of something after a certain amount of time', aliases=['timer', 'remind', 'rm'])
    async def reminder(self, ctx):
        if not ctx.invoked_subcommand:
            await ctx.reply('Invalid reminder command passed.')
            return
        tuple = self.bot.c.execute(
            'select Verified FROM main where Discord_UID = ?', (ctx.author.id,)
        ).fetchone()
        if not tuple:
            raise Exception('AccountNotLinked')
        if tuple[0] == 'False':
            raise Exception('EmailNotVerified')

    @reminder.command(name='add')
    async def add(self, ctx, message, time, repeat='False'):
        try:
            time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
        except:
            await ctx.reply('Time entered in the wrong format. Correct format: `YYYY-MM-DD HH:MM:SS`')
            return
        IST = pytz.timezone('Asia/Kolkata')
        time = IST.localize(time)
        datetime_ist = datetime.now(IST)
        if datetime_ist > time:
            await ctx.reply('Please input a time in the future.')
            return
        dict = {
            'author': ctx.author.id,
            'time': time,
            'message': message,
            'repeat': 'False',
            'channel': 0
        }
        if ctx.message.channel_mentions and ctx.author.guild_permissions.manage_channels:
            dict['channel'] = ctx.message.channel_mentions[0].id
        if repeat.lower() in ['false', 'daily', 'weekly', 'monthly', 'yearly']:
            dict['repeat'] = repeat
        self.data[str(int(list(self.data)[-1]) + 1)] = dict
        self.save()
        diff = str(time - datetime_ist).split(', ')
        remaining_time = []
        if len(diff) == 2:
            remaining_time.append(diff[0])
            diff = diff[1]
        else:
            diff = diff[0]
        diff = diff.split(':')
        remaining_time.append(f'{diff[0]} hour(s)')
        remaining_time.append(f'{int(diff[1])} minute(s)')
        remaining_time.append(f'{diff[2][:2]} second(s)')
        remaining_time = ', '.join(remaining_time)
        await ctx.reply(f'Reminder scheduled for {remaining_time} from now. ID: {list(dict)[0]}')

    def save(self):
        with open('db/reminders.json', 'w') as f:
            json.dump(self.data, f)

    async def reminder_loop(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                with open('db/reminders.json') as f:
                    data = json.load(f)
            except FileNotFoundError:
                data = {}
            IST = pytz.timezone('Asia/Kolkata')
            datetime_ist = datetime.now(IST)
            for i in data.copy():
                time = IST.localize(datetime.strptime(data[i]['time'], '%Y-%m-%d %H:%M:%S'))
                if time <= datetime_ist:
                    embed = discord.Embed(
                        title = 'Reminder',
                        description = data[i]['message'],
                        color = discord.Color.blurple()
                    )
                    channel = self.bot.get_channel(data[i]['channel'])
                    if channel:
                        await channel.send(embed=embed)
                    else:
                        author = self.bot.get_user(data[i]['author'])
                        await author.send(embed=embed)
                    if 'False' not in data[i]['repeat']:
                        if data[i]['repeat'] == 'daily':
                            time += timedelta(days=1)
                        elif data[i]['repeat'] == 'weekly':
                            time += timedelta(days=7)
                        elif data[i]['repeat'] == 'monthly':
                            time += timedelta(months=1)
                        elif data[i]['repeat'] == 'yearly':
                            time += timedelta(years=1)
                        data[i]['time'] = time.strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        del data[i]
                    with open('db/reminders.json', 'w') as f:
                        json.dump(data, f)
            await asyncio.sleep(1)

async def setup(bot):
    await bot.add_cog(Reminder(bot))
