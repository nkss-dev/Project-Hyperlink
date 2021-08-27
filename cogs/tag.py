import sqlite3, re

from utils.l10n import get_l10n
from utils.utils import getWebhook

from discord import utils, AllowedMentions
from discord.ext import commands

class Tag(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.conn = sqlite3.connect('db/details.db')
        self.c = self.conn.cursor()

    async def cog_check(self, ctx):
        self.l10n = get_l10n(ctx.guild.id, 'tag')
        return self.bot.verificationCheck(ctx)

    @commands.command(brief='Allows user to tag section/subsection roles')
    async def tag(self, ctx, *, content):
        """
        **Which all sections can I tag?**

        With this command, you're able to tag roles of subsections _given_\
        that the said subsection falls in the same section that you are in.
        This means that if you're in IT-A, you can tag `IT-A`, `IT-01`, `IT-02`\
        and `IT-03` but you can NOT tag `IT-B`, `IT-04`, `ME-B`, `PI-06`, etc

        **How can I tag?**

        Type your message normally after invoking this command like any other. \
        To tag an allowed section, simply precede the section/subsection with \
        the `@` symbol.

        The section/subsection follow the format as seen in the examples below:
        `Hello, @CE-01!`
        `Hey, @it-b. Please help me with this. I'm in @iT-05.`
        """

        webhook = await getWebhook(ctx.channel, self.bot.user)

        self.c.execute('SELECT Section FROM main where Discord_UID = (:uid)', {'uid': ctx.author.id})
        section = self.c.fetchone()[0]

        # Store roles that the user is allowed to tag
        if section[3] == 'A':
            validTags = [f'{section[:3]}01', f'{section[:3]}02', f'{section[:3]}03']
        elif section[3] == 'B':
            validTags = [f'{section[:3]}04', f'{section[:3]}05', f'{section[:3]}06']
        elif section[3] == 'C':
            validTags = [f'{section[:3]}07', f'{section[:3]}08', f'{section[:3]}09']
        validTags.append(section)

        # Loop through the string roles and mention the allowed and available ones
        for tag in re.findall('@[CEIMP][CEIST]-0[1-9]', content, flags=re.I):
            if tag[1:].upper() in validTags:
                try:
                    role = utils.get(ctx.guild.roles, name=tag[1:].upper())
                    content = content.replace(tag, role.mention, 1)
                except:
                    continue

        # Loop through the mentioned roles and remove the restricted ones
        for roleID in re.findall('<@&[0-9]{18}>', content):
            role = ctx.guild.get_role(int(roleID[3:-1]))

            if role.name in validTags:
                continue
            if role.mentionable:
                continue
            if ctx.author.guild_permissions.mention_everyone:
                continue

            content = content.replace(roleID, f'@{role.name}', 1)

        if ctx.author.guild_permissions.mention_everyone:
            allowed_mentions = AllowedMentions()
        else:
            allowed_mentions = AllowedMentions(everyone=False)

        await ctx.message.delete()
        await webhook.send(
            content.strip(),
            username = ctx.author.nick or ctx.author.name,
            avatar_url = ctx.author.avatar_url,
            allowed_mentions = allowed_mentions
        )

def setup(bot):
    bot.add_cog(Tag(bot))
