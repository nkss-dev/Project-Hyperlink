from discord import PermissionOverwrite
from discord.ext import commands


class Voice(commands.Cog):
    """Voice features"""

    def __init__(self, bot):
        self.bot = bot

    async def create_vc(self, member, category):
        vc = await member.guild.create_voice_channel(
            f"{member.display_name}\'s Party",
            category=category
        )
        await member.move_to(vc)
        self.bot.c.execute(
            'insert into voice (Voice_Channel, Owner) values (?,?)',
            (vc.id, member.id,)
        )
        self.bot.db.commit()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Called when a member changes their VoiceState"""
        if member.bot:
            return

        if before.channel == after.channel:
            return

        if before.channel:
            channel_id = self.bot.c.execute(
                'select Text_Channel from voice where Voice_Channel = ?',
                (before.channel.id,)
            ).fetchone()
            if channel_id and channel_id[0]:
                channel = member.guild.get_channel(channel_id[0])
                if before.channel.members:
                    await channel.set_permissions(member, overwrite=None)
                else:
                    await channel.delete()
                    self.bot.c.execute(
                        'update voice set Text_Channel = null where Text_Channel = ?',
                        (channel.id,)
                    )
                    self.bot.db.commit()

            if not before.channel.members:
                channel_ids = self.bot.c.execute(
                    'select Voice_Channel from voice where Owner not null'
                ).fetchall()
                print(before.channel.id)
                print(channel_ids)
                if (before.channel.id,) in channel_ids:
                    await before.channel.delete()
                    self.bot.c.execute(
                        'delete from voice where Voice_Channel = ?',
                        (before.channel.id,)
                    )
                    self.bot.db.commit()

        if not after.channel:
            return

        channel_id = self.bot.c.execute(
            'select Text_Channel from voice where Voice_Channel = ?',
            (after.channel.id,)
        ).fetchone()
        if channel_id and channel_id[0]:
            channel = member.guild.get_channel(channel_id[0])
            await channel.set_permissions(member, read_messages=True)
            return

        member_name = member.nick or member.name

        allow_text = self.bot.c.execute(
            'select Allow_Text from voice where Voice_Channel = ? and Create_vc = 0',
            (after.channel.id,)
        ).fetchone()
        if allow_text:
            overwrites = {
                member.guild.default_role: PermissionOverwrite(
                    read_messages=False, read_message_history=False
                ),
                member: PermissionOverwrite(read_messages=True)
            }
            channel = await member.guild.create_text_channel(
                f'party of {member_name}',
                overwrites=overwrites,
                category=after.channel.category
            )
            self.bot.c.execute(
                'update voice set Text_Channel = ? where Voice_Channel = ?',
                (channel.id, after.channel.id,)
            )
            self.bot.db.commit()
            return

        vc_enabled = self.bot.c.execute(
            'select Create_vc from voice where Voice_Channel = ?',
            (after.channel.id,)
        )
        if not vc_enabled:
            return

        await self.create_vc(member, after.channel.category)


def setup(bot):
    bot.add_cog(Voice(bot))