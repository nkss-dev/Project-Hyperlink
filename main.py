import discord, aiohttp, os, sqlite3, json, pytz, asyncio
from discord.utils import get
from discord.ext import commands
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

def get_prefix(client, message):
    with open('db/guilds.json', 'r') as f:
        prefixes = json.load(f)
    return prefixes[str(message.guild.id)]['prefix']

intents = discord.Intents.all()
client = commands.Bot(command_prefix=get_prefix, intents=intents)

@client.command(brief='Displays details of the user', aliases=['p'])
async def profile(ctx):
    """Displays details of the user related to the server and the college"""
    member = ctx.message.mentions
    if member and member[0] != ctx.author:
        try:
            with open('db/guilds.json', 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {str(ctx.guild.id): {'prefix': ['%'], 'mod_role': []}}
            with open('db/guilds.json', 'w') as f:
                json.dump(data, f)
        # Fetches the moderator roles set for that guild
        if mod_roles := [ctx.guild.get_role(role) for role in data[str(ctx.guild.id)]['mod_roles']]:
            flag = False
            for mod_role in mod_roles:
                if mod_role in ctx.author.roles:
                    flag = True
                    break
            # Exit if the author is not a moderator
            if not flag:
                await ctx.reply('You\'re not authorised to use this command.')
                return
        else:
            await ctx.send('No moderator role has been set for this guild. Set moderator roles using the `setmod` command.')
            return
        member = member[0]
    else:
        member = ctx.author
    conn = sqlite3.connect('db/details.db')
    c = conn.cursor()
    # Gets details of requested user from the database
    c.execute('SELECT * FROM main where Discord_UID = (:uid)', {'uid': member.id})
    tuple = c.fetchone()
    # Exit if the user was not found
    if not tuple:
        await ctx.send('The requested record wasn\'t found!')
        return
    # Creates a list of role objects of the user to display in the embed
    roles = ', '.join([role.mention for role in member.roles if tuple[2] != role.name and tuple[3] != role.name and '@everyone' != role.name])
    if not roles:
        roles = 'None taken'
    # Checking if the user has a verified email or not
    if tuple[11] == 'True':
        verification_status = ' <:verified:819460140247810059>'
    else:
        verification_status = ' <:notverified:819460105250537483>'
    # Creating the embed
    embed = discord.Embed(
        title = ' '.join([word[:1] + word[1:].lower() for word in tuple[4].split(' ')]) + verification_status,
        description = '**Roll Number: **' + str(tuple[1])
        + '\n**Section: **' + tuple[2] + tuple[3][4:]
        + '\n**Roles: **' + roles
        + '\n**Email: **' + tuple[6],
        colour = member.top_role.color
    )
    embed.set_author(name = str(member) + '\'s Profile', icon_url = member.avatar_url)
    embed.set_thumbnail(url = member.avatar_url)
    embed.set_footer(text = 'Joined at: ' + str(member.joined_at)[8:10] + '-' + str(member.joined_at)[5:7] + '-' + str(member.joined_at)[:4])
    await ctx.send(embed = embed)

@client.command(brief='Segregated display of the number of members')
async def memlist(ctx, batch: int=2024):
    """Displays the total number of members joined per section. Also displays the number of verified members on the server along with the total number of humans on the server"""
    conn = sqlite3.connect('db/details.db')
    c = conn.cursor()
    sections = ['CE-A', 'CE-B', 'CE-C', 'CS-A', 'CS-B', 'EC-A', 'EC-B', 'EC-C', 'EE-A', 'EE-B', 'EE-C', 'IT-A', 'IT-B', 'ME-A', 'ME-B', 'ME-C', 'PI-A', 'PI-B']
    total = []
    joined = []
    verified = []
    for section in sections:
        c.execute('SELECT count(*), count(Discord_UID) from main where Section = (:section) and Batch = (:batch)', {'section': section, 'batch': batch})
        tuple = c.fetchone()
        total.append(tuple[0])
        joined.append(tuple[1])
    for section in sections:
        c.execute('SELECT count(*) from main where Section = (:section) and Verified = "True" and Batch = (:batch)', {'section': section, 'batch': batch})
        tuple = c.fetchone()
        verified.append(tuple[0])
    c.execute('SELECT count(*), count(Discord_UID) from main where Batch = (:batch)', {'batch': batch})
    tuple = c.fetchone()
    total.append(tuple[0])
    joined.append(tuple[1])
    table =  '╭─────────┬────────┬───────────┬──────────╮\n'
    table += '│ Section │ Joined │ Remaining │ Verified │\n'
    table += '├─────────┼────────┼───────────┼──────────┤\n'
    previous = sections[0][:2]
    for section, num1, num2, verify in zip(sections, joined, total, verified):
        if section[:2] != previous[:2]:
            table += '├─────────┼────────┼───────────┼──────────┤\n'
        table += '│{:^9}│{:^8}│{:^11}│{:^10}│\n'.format(section, str(num1).zfill(2), str(num2-num1).zfill(2), str(verify).zfill(2))
        previous = section[:2]
    table += '├─────────┼────────┼───────────┼──────────┤\n'
    table += '│  Total  │{:^8}│{:^11}│{:^10}│\n'.format(str(sum(joined[:-1])).zfill(2), str(sum(total[:-1])-sum(joined[:-1])).zfill(2), str(sum(verified)).zfill(2))
    table += '╰─────────┴────────┴───────────┴──────────╯'
    embed = discord.Embed(
        description = f'```\n{table}```',
        color = discord.Color.blurple()
    )
    await ctx.send(embed=embed)

@client.command(brief='Allows user to tag section/subsection roles')
async def tag(ctx, content):
    """**How to use:**
    Now you're able to tag roles of subsections _given_ that the said subsection falls in the same section that you are in.
    That means that if you're in IT-A, you can tag `IT-A, IT-01, IT-02, ...` but you can NOT tag `IT-B, IT-06, ME-B, CE-01, PI-06, ...`

    **How do I tag? The normal tagging still doesn't work.**
    Here's how, you will have to precede your message with `%tag ` and type the role tag manually along with the message that you want to send.
    Examples:
    `%tag Hey @CS-01 can you solve this?`
    `%tag @it-a when's the due date of the assignment`
    Capitalization does NOT matter.

    **PS:** If you're found to abuse this facility, ie. spam tags or tag people for an unimportant reason, then this facility will be revoked for you and you may be banned temporarily. Though I'll try to avoid such things. (And you should too)"""

    sections = ['CE-A', 'CE-B', 'CE-C', 'CS-A', 'CS-B', 'EC-A', 'EC-B', 'EC-C', 'EE-A', 'EE-B', 'EE-C', 'IT-A', 'IT-B', 'ME-A', 'ME-B', 'ME-C', 'PI-A', 'PI-B']
    subsections = ['CE-01', 'CE-02', 'CE-03', 'CE-04', 'CE-05', 'CE-06', 'CE-07', 'CE-08', 'CE-09',
                'CS-01', 'CS-02', 'CS-03', 'CS-04', 'CS-05', 'CS-06',
                'EC-01', 'EC-02', 'EC-03', 'EC-04', 'EC-05', 'EC-06', 'EC-07', 'EC-08', 'EC-09',
                'EE-01', 'EE-02', 'EE-03', 'EE-04', 'EE-05', 'EE-06', 'EE-07', 'EE-08', 'EE-09',
                'IT-01', 'IT-02', 'IT-03', 'IT-04', 'IT-05', 'IT-06',
                'ME-01', 'ME-02', 'ME-03', 'ME-04', 'ME-05', 'ME-06', 'ME-07', 'ME-08', 'ME-09',
                'PI-01', 'PI-02', 'PI-03', 'PI-04', 'PI-05', 'PI-06'
            ]

    bool = False
    async with aiohttp.ClientSession() as session:
        # Checks if a webhook already exists for that channel
        webhooks = await ctx.channel.webhooks()
        for webhook in webhooks:
            if webhook.user == client.user:
                bool = True
                break
        # Creates a webhook if none exist
        if not bool:
            webhook = await ctx.channel.create_webhook(name='Webhook')
    if ctx.author.nick:
        username = ctx.author.nick
    else:
        username = str(ctx.author.name)
    conn = sqlite3.connect('db/details.db')
    c = conn.cursor()
    # Gets details of user from the database
    c.execute('SELECT Verified, Section FROM main where Discord_UID = (:uid)', {'uid': ctx.author.id})
    tuple = c.fetchone()
    if tuple[0] == 'False':
        await ctx.reply('Only members with a verified email can use this command.')
        raise Exception('Permission Denied (Absence of a verified email)')
    section = tuple[1]
    for i in content.split(' '):
        # Exit if the user tries to ping @everyone or @here
        if '@everyone' in i or '@here' in i:
            await ctx.send('You can\'t tag `@everyone` or `@here`')
            return
        # Skip to the next iteration if the current word doesn't contain a tag
        if not i or '@' not in i:
            continue
        i = i.replace('\\', '')
        # Loops through every tag in the word/phrase
        for j in i.split('@')[1:]:
            # Checks if a user has been tagged
            usertag = False
            for k in ctx.message.mentions:
                if str(k.id) in j:
                    usertag = True
            # Checks if a role has been tagged by its ID
            if '&' in j and int(j[1:-1]) in [role.id for role in ctx.guild.roles]:
                content = content.replace('\<@' + j, '@' + ctx.guild.get_role(int(j[1:-1])).name)
                j = j.replace(j, ctx.guild.get_role(int(j[1:-1])).name)
            # Skip to the next iteration if tagged section doesn't exist
            elif j[:4].upper() not in sections and j[:5].upper() not in subsections:
                continue
            # Skip to the next iteration if the tag is of a user
            if usertag:
                continue
            # Checks if the user belongs to the tagged section
            if j and ctx.author.guild_permissions.mention_everyone:
                if j[3] == '0':
                    content = content.replace('@' + j[:5], discord.utils.get(ctx.guild.roles, name = j[:5].strip().upper()).mention)
                elif j[3].upper() == section[3]:
                    content = content.replace('@' + j[:4], discord.utils.get(ctx.guild.roles, name = j[:4].strip().upper()).mention)
            elif j and j[:2].upper() not in section:
                await ctx.send('You can\'t tag sections other than your own!')
                return
            elif j and j[:2].upper() in section:
                # Checks if the tag is of a SubSection
                if j[3] == '0':
                    # Checks if the user belongs to the Section of the SubSection that they attempted to tag
                    if section[3] == 'A' and (j[4] == '1' or j[4] == '2' or j[4] == '3'):
                        content = content.replace('@' + j[:5], discord.utils.get(ctx.guild.roles, name = j[:5].strip().upper()).mention)
                    elif section[3] == 'B' and (j[4] == '4' or j[4] == '5' or j[4] == '6'):
                        content = content.replace('@' + j[:5], discord.utils.get(ctx.guild.roles, name = j[:5].strip().upper()).mention)
                    elif section[3] == 'C' and (j[4] == '7' or j[4] == '8' or j[4] == '9'):
                        content = content.replace('@' + j[:5], discord.utils.get(ctx.guild.roles, name = j[:5].strip().upper()).mention)
                    else:
                        await ctx.send('You can\'t tag sections other than your own!')
                        return
                elif j[3].upper() == section[3]:
                    content = content.replace('@' + j[:4], discord.utils.get(ctx.guild.roles, name = j[:4].strip().upper()).mention)
                else:
                    await ctx.send('You can\'t tag sections other than your own!')
                    return
    # Deletes the sent command and sends the new tagged version
    await ctx.message.delete()
    await webhook.send(content.strip(), username=username, avatar_url=ctx.author.avatar_url)

@client.command(brief='Nicks the user to their first name')
@commands.has_permissions(manage_nicknames=True)
async def nick(ctx):
    """Changes name of the user to their first name as in the database. Can only be used by members with the `Manage Nicknames` permission."""
    # Exit if no one was tagged
    if not ctx.message.mentions:
        await ctx.reply('Tag someone to reset their nickname.')
        return
    conn = sqlite3.connect('db/details.db')
    c = conn.cursor()
    for member in ctx.message.mentions:
        # Gets details of user from the database
        c.execute('SELECT Name FROM main where Discord_UID = (:uid)', {'uid': member.id})
        tuple = c.fetchone()
        # Exit if the user was not found
        if not tuple:
            await ctx.send(f'{member} does not exist in the database')
            return
        word = tuple[0].split(' ')[0]
        await member.edit(nick = word[:1] + word[1:].lower())
        await ctx.send(f'Changed the nick of `{member}` successfully.')

@client.command(brief='Gives invites of some servers', aliases=['inv'])
async def invite(ctx):
    servers = ['NITKKR\'24: https://discord.gg/4eF7R6afqv',
        'kkr++: https://discord.gg/epaTW7tjYR'
    ]
    embed = discord.Embed(
        title = 'Invites:',
        description = '\n'.join(servers),
        color = discord.Color.blurple()
    )
    await ctx.send(embed=embed)

@client.command(brief='Restarts the bot')
@commands.has_permissions(manage_guild=True)
async def restart(ctx):
    """Restarts the bot. Can only be used by members with the `Manage Server` permission."""
    await ctx.message.delete()
    await client.close()

async def reminder_loop():
    await client.wait_until_ready()
    while not client.is_closed():
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
                    description = message,
                    color = discord.Color.blurple()
                )
                channel = client.get_channel(data[i]['channel'])
                if channel:
                    await channel.send(embed=embed)
                else:
                    author = client.get_user(data[i]['author'])
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

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

client.loop.create_task(reminder_loop())
client.run(os.getenv('BOT_TOKEN'))
