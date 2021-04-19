import discord, os, sqlite3, json
from discord.ext import commands
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def get_prefix(client, message):
    with open('db/guilds.json', 'r') as f:
        prefixes = json.load(f)
    return prefixes[str(message.guild.id)]['prefix']

intents = discord.Intents.all()
client = commands.Bot(command_prefix=get_prefix, intents=intents)
client.launch_time = datetime.utcnow()

@client.event
async def on_ready():
    print(f'Logged on as {client.user}!\n')
    await client.change_presence(activity=discord.Game(f'@{client.user.name}'))

    default_details = {
        'prefix': ['%'],
        'mod_roles': [],
        'bot_role': 0,
        'logging_channel': [0, 0]
    }
    try:
        with open('db/guilds.json', 'r') as f:
            details = json.load(f)
        for guild in details:
            for key in default_details:
                if key not in details[guild]:
                    details[guild][key] = default_details[key]
        with open('db/guilds.json', 'w') as f:
            json.dump(details, f)
    except FileNotFoundError:
        # Creates the guilds.json file if it doesn't exist as it is essential for many cog's functioning
        data = dict([(guild.id, default_details) for guild in client.guilds])
        with open('db/guilds.json', 'w') as f:
            json.dump(data, f)

    # Loads all the cogs
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            client.load_extension(f'cogs.{filename[:-3]}')

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

client.run(os.getenv('BOT_TOKEN'))
