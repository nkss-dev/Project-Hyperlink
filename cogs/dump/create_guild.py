import discord
from discord.ext import commands

import sys
from utils.l10n import get_l10n

class Channels():
    def __init__(self, bot, guild, roles):
        self.bot = bot
        self.guild = guild
        muted = discord.PermissionOverwrite(
            send_messages=False,
            send_messages_in_threads=False,
            connect=False
        )

        self.categories = [
            {
                'name': 'INFO',
                'overwrites': {
                    roles['mod']: discord.PermissionOverwrite(send_messages=True, add_reactions=True),
                    roles['Robot Overlords']: discord.PermissionOverwrite(send_messages=True, add_reactions=True),
                    roles['Music Bot']: discord.PermissionOverwrite(read_messages=False),
                    roles['Not-Verified']: discord.PermissionOverwrite(read_messages=False),
                    guild.default_role: discord.PermissionOverwrite(send_messages=False, add_reactions=False),
                }
            },
            {
                'name': 'GENERAL',
                'overwrites': {
                    roles['Music Bot']: discord.PermissionOverwrite(read_messages=False),
                    roles['muted']: muted,
                    roles['Not-Verified']: discord.PermissionOverwrite(read_messages=False),
                }
            },
            {
                'name': 'TOPIC-WISE',
                'overwrites': {
                    roles['mod']: discord.PermissionOverwrite(read_messages=True),
                    roles['Robot Overlords']: discord.PermissionOverwrite(
                        read_messages=True,
                        send_messages=False
                    ),
                    roles['muted']: muted,
                    guild.default_role: discord.PermissionOverwrite(read_messages=False)
                }
            },
            {
                'name': 'HELP',
                'overwrites': {
                    roles['Robot Overlords']: discord.PermissionOverwrite(send_messages=False),
                    roles['Music Bot']: discord.PermissionOverwrite(read_messages=False),
                    roles["User's Bot"]: discord.PermissionOverwrite(read_messages=False),
                    roles['muted']: muted,
                    roles['Not-Verified']: discord.PermissionOverwrite(read_messages=False),
                }
            }
        ]

        self.text_channels = [
            # INFO
            {'name': 'rules', 'category': self.categories[0]['name']},
            {
                'name': 'announcements',
                'sync_permissions': True,
                'category': self.categories[0]['name'],
                'type': discord.ChannelType.news
            },
            {
                'name': 'drive-changelog',
                'sync_permissions': True,
                'category': self.categories[0]['name'],
                'type': discord.ChannelType.news
            },
            {
                'name': 'club-announcements',
                'sync_permissions': True,
                'category': self.categories[0]['name'],
                'type': discord.ChannelType.news
            },
            {
                'name': 'bot-updates',
                'sync_permissions': True,
                'category': self.categories[0]['name'],
                'type': discord.ChannelType.news
            },
            {
                'name': 'role-selection',
                'sync_permissions': True,
                'category': self.categories[0]['name']
            },
            {
                'name': 'suggestions',
                'sync_permissions': True,
                'category': self.categories[0]['name']
            },
            {
                'name': 'komedy',
                'sync_permissions': True,
                'category': self.categories[0]['name']
            },
            {
                'name': 'join-logs',
                'sync_permissions': True,
                'category': self.categories[0]['name']
            },

            # GENERAL
            {
                'name': 'chill-lounge',
                'topic': 'Speak',
                'sync_permissions': True,
                'category': self.categories[1]['name']
            },
            {
                'name': 'debate',
                'topic': 'Popular opinion? Unpopular opinion? All goes here!',
                'sync_permissions': True,
                'category': self.categories[1]['name']
            },
            {
                'name': 'games-central',
                'topic': 'Talk all games here!',
                'sync_permissions': True,
                'category': self.categories[1]['name']
            },
            {
                'name': 'meme-dump',
                'topic': 'Share memes here',
                'sync_permissions': True,
                'category': self.categories[1]['name']
            },
            {
                'name': 'sports',
                'topic': "Fight to death while deciding who's the better player",
                'sync_permissions': True,
                'category': self.categories[1]['name']
            },
            {
                'name': 'introduce-yourselves',
                'topic': 'Give a brief intro of yourself here so that everyone \
                    knows you just that little better. Please avoid conversations',
                'sync_permissions': True,
                'category': self.categories[1]['name'],
                'slowmode_delay': 10
            },

            # TOPIC-WISE
            {
                'name': 'heathen-lounge',
                'category': self.categories[2]['name'],
                'overwrites': self.categories[2]['overwrites'].copy().update({
                    roles['Heathen']: discord.PermissionOverwrite(read_messages=True)
                })
            },
            {
                'name': 'stonks',
                'category': self.categories[2]['name'],
                'overwrites': self.categories[2]['overwrites'].copy().update({
                    roles['Trader']: discord.PermissionOverwrite(read_messages=True)
                })
            },
            {
                'name': 'weeb-lounge',
                'category': self.categories[2]['name'],
                'overwrites': self.categories[2]['overwrites'].copy().update({
                    roles['Weeb']: discord.PermissionOverwrite(read_messages=True)
                })
            },

            # HELP
            {
                'name': 'help',
                'topic': '',
                'sync_permissions': True,
                'category': self.categories[3]['name']
            },
        ]

        self.voice_channels = [
            {
                'name': 'chill lounge vc',
                'sync_permissions': True,
                'category': self.categories[1]['name']
            }
        ]

    async def edit_tc(self, **kwargs):
        if not (channel := discord.utils.get(self.guild.channels, name=kwargs['name'])):
            channel = await self.guild.create_text_channel(
                name=kwargs.pop('name'),
                category=kwargs.pop('category')
            )
        for key, value in kwargs.copy().items():
            if value == getattr(channel, key):
                kwargs.pop(key)
        self.tc_channels.append((channel, kwargs))

    async def category(self):
        for i, category in enumerate(self.categories):
            # Create category if not found
            if not (existing_cat := discord.utils.get(self.guild.categories, name=category['name'])):
                existing_cat = await self.guild.create_category(name=category.pop('name'))

            category['position'] = i

            # Remove values that do not need to be changed
            for key, value in category.copy().items():
                if value == getattr(existing_cat, key):
                    category.pop(key)

            await existing_cat.edit(**category)

    async def tc(self):
        for i, text_channel in enumerate(self.text_channels):
            # Create channel if not found
            if not (tc := discord.utils.get(self.guild.text_channels, name=text_channel['name'])):
                tc = await self.guild.create_text_channel(name=kwargs.pop('name'))

            text_channel['position'] = i

            # Remove values that do not need to be changed
            for key, value in text_channel.copy().items():
                if key == 'sync_permissions':
                    if value == getattr(tc, 'permissions_synced'):
                        text_channel.pop(key)
                elif value == getattr(tc, key):
                    text_channel.pop(key)

            await tc.edit(**text_channel)

    async def vc(self):
        for i, voice_channel in enumerate(self.voice_channels):
            # Create channel if not found
            if not (vc := discord.utils.get(self.guild.voice_channels, name=voice_channel['name'])):
                vc = await self.guild.create_voice_channel(name=kwargs.pop('name'))

            voice_channel['position'] = i

            # Remove values that do not need to be changed
            for key, value in voice_channel.copy().items():
                if key == 'sync_permissions':
                    if value == getattr(vc, 'permissions_synced'):
                        voice_channel.pop(key)
                elif value == getattr(vc, key):
                    voice_channel.pop(key)

            await vc.edit(**voice_channel)

    async def run(self):
        await self.category()

        for i, channel in enumerate(self.text_channels):
            self.text_channels[i]['category'] = discord.utils.get(
                self.guild.categories, name=self.text_channels[i]['category']
            )

        for i, channel in enumerate(self.voice_channels):
            self.voice_channels[i]['category'] = discord.utils.get(
                self.guild.categories, name=self.voice_channels[i]['category']
            )

        if self.guild.rules_channel:
            await self.guild.rules_channel.edit(**self.text_channels[0])

        await self.tc()
        await self.vc()

class Roles():
    def __init__(self, bot):
        self.bot = bot
        self.roles = []

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
            ('CE-01', 0x1abc9c), ('CE-02', 0x9740f8), ('CE-03', 0xf17723),
            ('CE-04', 0x2ecc71), ('CE-05', 0x3498db), ('CE-06', 0xff2020),
            ('CE-07', 0xe74c3c), ('CE-08', 0x6cff02), ('CE-09', 0xf80bb4),

            ('CS-01', 0x1abc9c), ('CS-02', 0x9740f8), ('CS-03', 0xf17723),
            ('CS-04', 0x2ecc71), ('CS-05', 0x3498db), ('CS-06', 0xff2020),

            ('EC-01', 0x1abc9c), ('EC-02', 0x9740f8), ('EC-03', 0xf17723),
            ('EC-04', 0x2ecc71), ('EC-05', 0x3498db), ('EC-06', 0xff2020),
            ('EC-07', 0xe74c3c), ('EC-08', 0x6cff02), ('EC-09', 0xf80bb4),

            ('EE-01', 0x1abc9c), ('EE-02', 0x9740f8), ('EE-03', 0xf17723),
            ('EE-04', 0x2ecc71), ('EE-05', 0x3498db), ('EE-06', 0xff2020),
            ('EE-07', 0xe74c3c), ('EE-08', 0x6cff02), ('EE-09', 0xf80bb4),

            ('IT-01', 0x1abc9c), ('IT-02', 0x9740f8), ('IT-03', 0xf17723),
            ('IT-04', 0x2ecc71), ('IT-05', 0x3498db), ('IT-06', 0xff2020),

            ('ME-01', 0x1abc9c), ('ME-02', 0x9740f8), ('ME-03', 0xf17723),
            ('ME-04', 0x2ecc71), ('ME-05', 0x3498db), ('ME-06', 0xff2020),
            ('ME-07', 0xe74c3c), ('ME-08', 0x6cff02), ('ME-09', 0xf80bb4),

            ('PI-01', 0x1abc9c), ('PI-02', 0x9740f8), ('PI-03', 0xf17723),
            ('PI-04', 0x2ecc71), ('PI-05', 0x3498db), ('PI-06', 0xff2020)
        )

        self.hostels = (
            'H1', 'H2', 'H3', 'H4', 'H5', 'H6', 'H7', 'H8', 'H9', 'H10', 'H11',
            'GH1', 'GH2', 'GH3', 'GH4'
        )

        groups = self.bot.c.execute(
            'select name, alias from groups order by name'
        ).fetchall()
        self.clubs = [group[1] or group[0] for group in groups]

        self.generals = (
            'Cinephilic', 'DJ', 'Gearhead', 'Heathen', 'Trader', 'Weeb'
        )

        self.games = (
            'Age of Empires', 'Among Us', "Assassin's Creed",
            'Chess', 'Clash of Clans', 'Clash Royale', 'COD', 'CSGO',
            'Fortnite', 'Genshin Impact', 'GTAV', 'Minecraft', 'osu!',
            'Paladins', 'PUBG', 'Rise of Nations', 'Rocket League',
            'skribbl.io', 'Valorant'
        )

        self.miscs = (
            ('muted', 0xff0000), ('Not-Verified', discord.Color.default())
        )

    async def edit(self, **kwargs):
        if not (role := discord.utils.get(self.guild.roles, name=kwargs['name'])):
            role = await self.guild.create_role()
            if self.guild.me != self.guild.owner:
                await role.edit(position=self.guild.me.top_role.position - 1)
        for key, value in kwargs.copy().items():
            if key == 'color' and isinstance(value, int) and value == getattr(role, key).value:
                kwargs.pop(key)
            elif value == getattr(role, key):
                kwargs.pop(key)
        self.roles.append((role, kwargs))

    def everyone(self, perms: discord.Permissions=discord.Permissions()):
        perms.add_reactions = True
        perms.attach_files = True
        perms.change_nickname = True
        perms.connect = True
        perms.create_private_threads = True
        perms.create_public_threads = True
        perms.embed_links = True
        perms.external_emojis = True
        perms.external_stickers = True
        perms.read_message_history = True
        perms.read_messages = True
        perms.request_to_speak = True
        perms.send_messages = True
        perms.send_messages_in_threads = True
        perms.speak = True
        perms.stream = True
        perms.use_voice_activation = True
        perms.view_guild_insights = True

        return perms

    async def mod(self):
        perms = self.guild.default_role.permissions

        perms.ban_members = True
        perms.deafen_members = True
        perms.kick_members = True
        perms.manage_channels = True
        perms.manage_emojis = True
        perms.manage_emojis_and_stickers = True
        perms.manage_events = True
        perms.manage_guild = True
        perms.manage_messages = True
        perms.manage_nicknames = True
        perms.manage_permissions = True
        perms.manage_roles = True
        perms.manage_threads = True
        perms.manage_webhooks = True
        perms.mention_everyone = True
        perms.move_members = True
        perms.mute_members = True
        perms.use_slash_commands = True
        perms.view_audit_log = True

        kwargs = {
            'name': 'mod',
            'permissions': perms,
            'color': 0xe61efa
        }
        await self.edit(**kwargs)

        perms = self.guild.default_role.permissions
        perms.deafen_members = True
        perms.manage_messages = True
        perms.move_members = True
        perms.mute_members = True

        kwargs = {
            'name': 'Ainvayi Mod',
            'permissions': perms,
            'color': 0x8e4af4
        }
        await self.edit(**kwargs)

    async def botRoles(self):
        # Default bot role
        kwargs = {
            'name': 'Robot Overlords',
            'permissions': self.guild.default_role.permissions,
            'color': 0x118df0
        }
        await self.edit(**kwargs)

        # Music bot role
        kwargs['name'] = 'Music Bot'
        await self.edit(**kwargs)

        # User's bot role
        kwargs['name'] = "User's Bot"
        await self.edit(**kwargs)

    async def section(self):
        for role_name in self.sections:
            kwargs = {
                'name': role_name,
                'permissions': self.guild.default_role.permissions,
                'color': discord.Color.gold(),
                'hoist': True
            }
            await self.edit(**kwargs)

    async def subsection(self):
        for role_name, color in self.subsections:
            kwargs = {
                'name': role_name,
                'permissions': self.guild.default_role.permissions,
                'color': color
            }
            await self.edit(**kwargs)

    async def CR(self):
        kwargs = {
            'name': 'CR',
            'permissions': self.guild.default_role.permissions,
            'color': 0x1f8b4c,
            'mentionable': True
        }
        await self.edit(**kwargs)

    async def hostel(self):
        for role_name in self.hostels:
            kwargs = {
                'name': role_name,
                'permissions': self.guild.default_role.permissions,
                'color': 0x0082ff
            }
            await self.edit(**kwargs)

    async def club(self):
        for role_name in self.clubs:
            kwargs = {
                'name': role_name,
                'permissions': self.guild.default_role.permissions,
                'color': discord.Color.teal(),
                'mentionable': True
            }
            await self.edit(**kwargs)

    async def general(self):
        for role_name in self.generals:
            kwargs = {
                'name': role_name,
                'permissions': self.guild.default_role.permissions,
                'color': discord.Color.magenta(),
                'mentionable': True
            }
            await self.edit(**kwargs)

    async def game(self):
        for role_name in self.games:
            kwargs = {
                'name': role_name,
                'permissions': self.guild.default_role.permissions,
                'color': discord.Color.dark_gold(),
                'mentionable': True
            }
            await self.edit(**kwargs)

    async def misc(self):
        for role_name, color in self.miscs:
            kwargs = {
                'name': role_name,
                'permissions': self.guild.default_role.permissions,
                'color': color,
                'mentionable': True
            }
            await self.edit(**kwargs)

    async def run(self, guild: discord.Guild):
        self.guild = guild

        await self.guild.default_role.edit(permissions=self.everyone())

        await self.mod()

        if self.guild.premium_subscriber_role:
            self.roles.append([self.guild.premium_subscriber_role, {}])

        await self.botRoles()
        await self.subsection()
        await self.section()
        await self.CR()
        await self.hostel()
        await self.club()
        await self.general()
        await self.game()
        await self.misc()

        roles = {}
        pos = len(guild.roles) - 2
        for role, kwargs in self.roles:
            if kwargs or (not kwargs and pos != role.position):
                print(pos, role.position, role)
                await role.edit(**kwargs, position=pos)
            roles[role.name] = role
            pos -= 1

        self.roles = []

        return roles

class Guild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # self.roles = Roles(self.bot)

    async def cog_check(self, ctx) -> bool:
        self.l10n = get_l10n(ctx.guild.id if ctx.guild else 0, 'owner')
        return await commands.is_owner().predicate(ctx)

    @commands.group(invoke_without_command=True)
    async def guild(self, ctx):
        """Command group for guild create/sync commands"""
        await ctx.send_help(ctx.command)

    @guild.command()
    async def emojis(self, ctx):
        """Send guild emojis"""
        for emoji in ctx.guild.emojis:
            print(emoji)

    @guild.command()
    async def create(self, ctx, name: str=None, template=None):
        """Create a guild from scratch or from a given template"""
        guild = await self.bot.create_guild(name=name or 'Test', region=discord.VoiceRegion.india)

        category = await guild.create_category('INFO')
        channel = await guild.create_text_channel('hmm', category=category)
        invite = await channel.create_invite(max_uses=1)
        await ctx.send(invite)

        await self.roles.run(guild)

    @guild.command()
    async def delete(self, ctx):
        await ctx.guild.delete()

    @guild.command()
    async def sync(self, ctx, guild: discord.Guild=None):
        """Sync given guild to default settings"""
        guild = guild or ctx.guild

        if guild.me != guild.owner and guild.me.top_role != guild.roles[-1]:
            await ctx.send(self.l10n.format_value('top-role-not-highest'))
            return

        if 'COMMUNITY' not in guild.features:
            await ctx.send(self.l10n.format_value('enable-community'))
            return

        # roles = await self.roles.run(guild)
        await Channels(self.bot, guild, roles).run()
        await ctx.send(self.l10n.format_value('sync-success'))  # Guild roles synced successfully

def setup(bot):
    bot.add_cog(Guild(bot))
