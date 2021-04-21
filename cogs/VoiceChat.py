import discord, json
from discord.ext import commands

class VoiceChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            with open('db/VCs.json') as f:
                self.data = json.load(f)
        except FileNotFoundError:
            self.data = {
                'vc_enabled_channels': [],
                'party_vchannels': [],
                'allow_text': {},
                'text_enabled_channels': [],
                'party_tchannels': {}
            }

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
        if before.channel and before.channel != after.channel:
            if not before.channel.members:
                if str(before.channel.id) in self.data['party_tchannels']:
                    await self.bot.get_channel(self.data['party_tchannels'][str(before.channel.id)]).delete()
                    del self.data['party_tchannels'][str(before.channel.id)]
                    self.save()
                if before.channel.id in self.data['party_vchannels']:
                    await before.channel.delete()
                    self.data['party_vchannels'].remove(before.channel.id)
                    self.save()
            if str(before.channel.id) in self.data['party_tchannels']:
                tc = self.bot.get_channel(self.data['party_tchannels'][str(before.channel.id)])
                await tc.set_permissions(member, overwrite=None)
        if not after.channel:
            return
        if member.nick:
            member_name = member.nick
        else:
            member_name = member.name
        if str(after.channel.id) in self.data['party_tchannels']:
            tc = self.bot.get_channel(self.data['party_tchannels'][str(after.channel.id)])
            await tc.set_permissions(member, read_messages=True)
            return
        if after.channel.id in self.data['text_enabled_channels'] or (self.data['allow_text'][str(member.guild.id)] and after.channel.id in self.data['party_vchannels']):
            overwrites = {
                member.guild.default_role: discord.PermissionOverwrite(read_messages=False, read_message_history=False),
                member: discord.PermissionOverwrite(read_messages=True)
            }
            tc = await member.guild.create_text_channel(f'party of {member_name}', overwrites=overwrites, category=after.channel.category)
            self.data['party_tchannels'][str(after.channel.id)] = tc.id
            self.save()
            return
        if after.channel.id not in self.data['vc_enabled_channels']:
            return
        vc = await member.guild.create_voice_channel(f'{member_name}\'s Party', category=after.channel.category)
        if vc.id not in self.data['party_vchannels']:
            self.data['party_vchannels'].append(vc.id)
            self.save()
        await member.move_to(vc)

    def save(self):
        with open('db/VCs.json', 'w') as f:
            json.dump(self.data, f)

def setup(bot):
    bot.add_cog(VoiceChat(bot))
