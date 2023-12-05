import discord
from discord.ext import commands


class Setup(commands.Cog):
    """Bot owner commands"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def rules(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        general_rules = discord.Embed(
            title='General Rules', color=discord.Color.blurple()
        )
        vc_rules = discord.Embed(
            title='Voice Channel Rules', color=discord.Color.blurple()
        )

        general_rules_dict = {
            'Pings': 'Do not ping roles unnecessarily. Any unsolicited member pings is to be dealt by the pinged member.',
            'NSFW/NSFL': 'No NSFW/NSFL content or discussions are allowed outside of the designated channel(s).',
            'Nickname/Usernames': "Please avoid offensive or otherwise annoying username/nicknames. If it's difficult to mention, don't use it here.",
            'Raids/Spam': 'Any user found to be participating in raiding or mass spamming this server will result in an immediate ban.',
            'Be civil': "Maintain courteous human behaviour. Your freedom ends where another's begins.",
            'Keep the chat clean': 'Do not discuss politics outside of the designated channel(s). Discussion of religion is strictly prohibited.',
            'No advertising': 'No unsolicited advertising or any kind of promotions within the server.',
            'Spoiler discussions': 'Refrain from discussing spoilers about games, movies and other media. If discussing spoilers, appropriately use `||the spoiler tag||`. If in an image, check the mark image as spoiler before posting.',
            'No impersonations': 'If you are found to have been impersonating another student, your account will be banned permanently.',
            'Who decides right and wrong?': 'Mods will have the final say in any decision.',
        }
        vc_rules_dict = {
            'No loud noises': 'Do not intentionally annoy members with voice or music bots',
            "Don't troll": "Don't play troll songs or sounds",
            "Don't move or skip songs": "When with a music bot, don't move/skip other's music in the queue unless it was purposely played to troll or be annoying.",
        }

        for i, (rule, desc) in enumerate(general_rules_dict.items(), start=1):
            general_rules.add_field(
                name=f'{i}. {rule}', value=desc, inline=False
            )
        for i, (rule, desc) in enumerate(vc_rules_dict.items(), start=1):
            vc_rules.add_field(
                name=f'{i}. {rule}', value=desc, inline=False
            )

        await channel.send(embeds=[general_rules, vc_rules])
        await ctx.message.delete()

    @commands.command(aliases=['srs'])
    async def self_roles_setup(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        embed = discord.Embed(
            title='Self Roles',
            description='''
                Give yourself a role by reacting to the corresponding emote in the following messages.

                Most of these roles unlock certain text/voice channels for that specific role. If you feel like that category is proving to be rather irrelevant for your tastes, you can get rid of that role by removing your reaction sticker from the message that you took it from initially.

                These categories are being role specific so as to not clutter the server with channels for those who don't use them.
            ''',
            color=discord.Color.blurple()
        )
        await channel.send(embed=embed)
        await channel.send('**General Roles:**')
        await channel.send('**Games:**')


async def setup(bot):
    await bot.add_cog(Setup(bot))
