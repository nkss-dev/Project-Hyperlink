import json

from discord import PermissionOverwrite
from discord.ext import commands

class VoiceChat(commands.Cog):
    """Voice features"""

    def __init__(self, bot):
        self.bot = bot

        with open('db/VCs.json') as f:
            self.VCs = json.load(f)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """invoked when a member changes their VoiceState"""
        if member.bot:
            return

        if before.channel and before.channel != after.channel:
            if not before.channel.members:
                if str(before.channel.id) in self.VCs['party_tchannels']:
                    await member.guild.get_channel(self.VCs['party_tchannels'][str(before.channel.id)]).delete()
                    del self.VCs['party_tchannels'][str(before.channel.id)]
                    self.save()
                if before.channel.id in self.VCs['party_vchannels']:
                    await before.channel.delete()
                    self.VCs['party_vchannels'].remove(before.channel.id)
                    self.save()
            if str(before.channel.id) in self.VCs['party_tchannels']:
                tc = member.guild.get_channel(self.VCs['party_tchannels'][str(before.channel.id)])
                await tc.set_permissions(member, overwrite=None)
        if not after.channel:
            return
        if member.nick:
            member_name = member.nick
        else:
            member_name = member.name
        if str(after.channel.id) in self.VCs['party_tchannels']:
            tc = member.guild.get_channel(self.VCs['party_tchannels'][str(after.channel.id)])
            await tc.set_permissions(member, read_messages=True)
            return
        if after.channel.id in self.VCs['text_enabled_channels'] or (member.guild.id in self.VCs['allow_text'] and after.channel.id in self.VCs['party_vchannels']):
            overwrites = {
                member.guild.default_role: PermissionOverwrite(read_messages=False, read_message_history=False),
                member: PermissionOverwrite(read_messages=True)
            }
            tc = await member.guild.create_text_channel(f'party of {member_name}', overwrites=overwrites, category=after.channel.category)
            self.VCs['party_tchannels'][str(after.channel.id)] = tc.id
            self.save()
            return
        if after.channel.id not in self.VCs['vc_enabled_channels']:
            return
        vc = await member.guild.create_voice_channel(f'{member_name}\'s Party', category=after.channel.category)
        if vc.id not in self.VCs['party_vchannels']:
            self.VCs['party_vchannels'].append(vc.id)
            self.save()
        await member.move_to(vc)

    def save(self):
        with open('db/VCs.json', 'w') as f:
            json.dump(self.VCs, f)

async def setup(bot):
    await bot.add_cog(VoiceChat(bot))
