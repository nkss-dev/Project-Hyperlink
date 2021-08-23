from utils.l10n import get_l10n
from utils.utils import getWebhook

from discord import utils
from discord.ext import commands

class Tag(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.sections = (
            'CE-A', 'CE-B', 'CE-C',
            'CS-A', 'CS-B',
            'EC-A', 'EC-B', 'EC-C',
            'EE-A', 'EE-B', 'EE-C',
            'IT-A', 'IT-B',
            'ME-A', 'ME-B', 'ME-C',
            'PI-A', 'PI-B'
        )

        self.subsections = (
            'CE-01', 'CE-02', 'CE-03', 'CE-04', 'CE-05', 'CE-06', 'CE-07', 'CE-08', 'CE-09',
            'CS-01', 'CS-02', 'CS-03', 'CS-04', 'CS-05', 'CS-06',
            'EC-01', 'EC-02', 'EC-03', 'EC-04', 'EC-05', 'EC-06', 'EC-07', 'EC-08', 'EC-09',
            'EE-01', 'EE-02', 'EE-03', 'EE-04', 'EE-05', 'EE-06', 'EE-07', 'EE-08', 'EE-09',
            'IT-01', 'IT-02', 'IT-03', 'IT-04', 'IT-05', 'IT-06',
            'ME-01', 'ME-02', 'ME-03', 'ME-04', 'ME-05', 'ME-06', 'ME-07', 'ME-08', 'ME-09',
            'PI-01', 'PI-02', 'PI-03', 'PI-04', 'PI-05', 'PI-06'
        )

    async def cog_check(self, ctx):
        self.l10n = get_l10n(ctx.guild.id, 'tag')
        return self.bot.verificationCheck(ctx)

    @commands.command(brief='Allows user to tag section/subsection roles')
    async def tag(self, ctx, *, content):
        """With this command, you're able to tag roles of subsections _given_ that the said subsection falls in the same section that you are in.
        That means that if you're in IT-A, you can tag `IT-A, IT-01, IT-02 and IT-03` but you can NOT tag `IT-B, IT-04, ME-B, CE-01, PI-06, ...`

        **PS:** If you're found to abuse this facility, ie. spam tags and/or tag people for an unimportant reason, then this facility will be revoked for you and you will face consequences based on the severity of the abuse."""

        webhook = await getWebhook(ctx.channel, self.bot.user)

        section = tuple[1]
        for i in content.split(' '):
            # Exit if the user tries to ping @everyone or @here
            if '@everyone' in i or '@here' in i:
                await ctx.send(self.l10n.format_value('tag-everyone-invalid'))
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
                elif j[:4].upper() not in self.sections and j[:5].upper() not in self.subsections:
                    continue
                # Skip to the next iteration if the tag is of a user
                if usertag:
                    continue
                # Checks if the user belongs to the tagged section
                if j and ctx.author.guild_permissions.mention_everyone:
                    if j[3] == '0':
                        content = content.replace('@' + j[:5], utils.get(ctx.guild.roles, name = j[:5].strip().upper()).mention)
                    elif j[3].upper() == section[3]:
                        content = content.replace('@' + j[:4], utils.get(ctx.guild.roles, name = j[:4].strip().upper()).mention)
                elif j and j[:2].upper() not in section:
                    await ctx.send(self.l10n.format_value('tag-other-section-invalid'))
                    return
                elif j and j[:2].upper() in section:
                    # Checks if the tag is of a SubSection
                    if j[3] == '0':
                        # Checks if the user belongs to the Section of the SubSection that they attempted to tag
                        if section[3] == 'A' and (j[4] == '1' or j[4] == '2' or j[4] == '3'):
                            content = content.replace('@' + j[:5], utils.get(ctx.guild.roles, name = j[:5].strip().upper()).mention)
                        elif section[3] == 'B' and (j[4] == '4' or j[4] == '5' or j[4] == '6'):
                            content = content.replace('@' + j[:5], utils.get(ctx.guild.roles, name = j[:5].strip().upper()).mention)
                        elif section[3] == 'C' and (j[4] == '7' or j[4] == '8' or j[4] == '9'):
                            content = content.replace('@' + j[:5], utils.get(ctx.guild.roles, name = j[:5].strip().upper()).mention)
                        else:
                            await ctx.send(self.l10n.format_value('tag-other-section-invalid'))
                            return
                    elif j[3].upper() == section[3]:
                        content = content.replace('@' + j[:4], utils.get(ctx.guild.roles, name = j[:4].strip().upper()).mention)
                    else:
                        await ctx.send(self.l10n.format_value('tag-other-section-invalid'))
                        return

        await ctx.message.delete()
        await webhook.send(
            content.strip(),
            username = ctx.author.nick or ctx.author.name,
            avatar_url = ctx.author.avatar_url
        )

def setup(bot):
    bot.add_cog(Tag(bot))
