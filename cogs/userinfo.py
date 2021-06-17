import discord, json, sqlite3
from datetime import datetime
from discord.ext import commands

class UserInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open('db/guilds.json', 'r') as f:
            self.data = json.load(f)
        with open('db/emojis.json', 'r') as f:
            self.emojis = json.load(f)['utility']

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

    @commands.command(name='profile', brief='Displays details of the user', aliases=['p'])
    async def profile(self, ctx, *, member: discord.Member=None):
        """Displays details of the user related to the server and the college"""
        member = member or ctx.author
        if not await self.check(ctx, member):
            return
        # Gets details of requested user from the database
        self.c.execute('SELECT Roll_Number, Section, SubSection, Name, Institute_Email, Verified FROM main where Discord_UID = (:uid)', {'uid': member.id})
        tuple = self.c.fetchone()
        # Exit if the user was not found
        if not tuple:
            await ctx.reply('The requested record wasn\'t found!')
            return
        # Creates a list of role objects of the user to display in the embed
        ignored_roles = [tuple[1], tuple[2], '@everyone']
        user_roles = [role.mention for role in member.roles if role.name not in ignored_roles]
        user_roles.reverse()
        user_roles = ', '.join(user_roles)
        if not user_roles:
            user_roles = 'None taken'
        # Checking if the user has a verified email or not
        status = ' '
        if tuple[5] == 'True':
            status += self.emojis['verified']
        else:
            status += self.emojis['not-verified']
        # Creating the embed
        embed = discord.Embed(
            title = ' '.join([word[:1] + word[1:].lower() for word in tuple[3].split(' ')]) + status,
            description = f'**Roll Number:** {tuple[0]}'
            + f'\n**Section:** {tuple[1]}{tuple[2][4:]}'
            + f'\n**Roles:** {user_roles}'
            + f'\n**Email:** {tuple[4]}',
            colour = member.top_role.color
        )
        embed.set_author(name = f'{member}\'s Profile', icon_url = member.avatar_url)
        embed.set_thumbnail(url = member.avatar_url)
        join_date = member.joined_at.strftime('%b %d, %Y')
        embed.set_footer(text = f'Joined at: {join_date}')
        await ctx.send(embed=embed)

    @commands.command(name='nick', brief='Nicks a user to their first name')
    @commands.has_permissions(change_nickname=True)
    async def nick(self, ctx, member: discord.Member=None):
        """Changes name of the user to their first name as in the database. Can only be used by members with the `Manage Nicknames` permission."""
        member = member or ctx.author
        if not await self.check(ctx, member):
            return
        self.c.execute('SELECT Name FROM main where Discord_UID = (:uid)', {'uid': member.id})
        tuple = self.c.fetchone()
        # Exit if the user was not found
        if not tuple:
            await ctx.reply(f'`{member}` does not exist in the database')
            return
        old_nick = member.nick
        word = tuple[0].split(' ')[0]
        await member.edit(nick = word[:1] + word[1:].lower())
        await ctx.reply(f'Changed the nick of `{member}` from `{old_nick}` to `{member.nick}` successfully.')

    async def check(self, ctx, member):
        if member != ctx.author:
            if ctx.author.guild_permissions.manage_nicknames:
                return True
            # Fetches the moderator roles set for that guild
            if mod_roles := [ctx.guild.get_role(role) for role in self.data[str(ctx.guild.id)]['mod_roles']]:
                flag = False
                for mod_role in mod_roles:
                    if mod_role in ctx.author.roles:
                        flag = True
                        break
                # Exit if the author is not a moderator
                if not flag:
                    await ctx.reply('You\'re not authorised to use this command.')
                    return False
            else:
                await ctx.send('No moderator role has been set for this guild. Set moderator roles using the `setmod` command.')
                return False
        return True

def setup(bot):
    bot.add_cog(UserInfo(bot))
