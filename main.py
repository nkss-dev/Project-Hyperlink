import discord, os, sqlite3, json
from discord.utils import get
from discord.ext import commands
from dotenv import load_dotenv

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

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')

client.run(os.getenv('BOT_TOKEN'))
