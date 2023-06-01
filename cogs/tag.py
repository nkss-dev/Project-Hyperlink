import re

from discord import utils, AllowedMentions
from discord.ext import commands

import cogs.checks as checks
from utils.utils import get_any_webhook


class Tag(commands.Cog):
    """Tag section/sub-sections"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @checks.is_verified()
    @commands.guild_only()
    async def tag(self, ctx, *, content: str):
        """Allow the user to tag section/sub-section roles

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
        `Hey, @it-b; please help me with this. I'm in @iT-05.`
        """
        webhook = await get_any_webhook(
            channel=ctx.channel,
            member=ctx.guild.me,
            reason="Send messages that tag section roles",
        )

        section, batch = await self.bot.pool.fetchrow(
            "SELECT section, batch FROM student WHERE discord_uid = $1", ctx.author.id
        )

        # Store roles that the user is allowed to tag
        section, *sub_secs = await self.bot.pool.fetchrow(
            """
            SELECT
                section,
                ARRAY_AGG(DISTINCT sub_section)
            FROM
                student
            WHERE
                section = $1
                AND batch = $2
            GROUP BY
                section
            """,
            section,
            batch,
        )
        valid_tags = section, *sub_secs

        if result := re.findall("@[CEIMP][CEIST]-0[1-9]", content, flags=re.I):
            tags = result
        else:
            tags = []
        if result := re.findall("@[CEIMP][CEIST]-[ABC]", content, flags=re.I):
            tags.extend(result)

        # Loop through the string roles and mention the allowed and available ones
        for tag in tags:
            if tag[1:].upper() in valid_tags:
                role = utils.get(ctx.guild.roles, name=tag[1:].upper())
                if role:
                    content = content.replace(tag, role.mention, 1)

        # Loop through the mentioned roles and remove the restricted ones
        for roleID in re.findall("<@&[0-9]{18}>", content):
            role = ctx.guild.get_role(int(roleID[3:-1]))

            if role.name in valid_tags:
                continue
            if role.mentionable:
                continue
            if ctx.author.guild_permissions.mention_everyone:
                continue

            content = content.replace(roleID, f"@{role.name}", 1)

        if ctx.author.guild_permissions.mention_everyone:
            allowed_mentions = AllowedMentions()
        else:
            allowed_mentions = AllowedMentions(everyone=False)

        await ctx.message.delete()
        await webhook.send(
            content.strip(),
            username=ctx.author.display_name,
            avatar_url=ctx.author.avatar.url,
            allowed_mentions=allowed_mentions,
        )


async def setup(bot):
    await bot.add_cog(Tag(bot))
