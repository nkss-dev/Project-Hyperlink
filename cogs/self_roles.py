import json
import sqlite3
from asyncio import TimeoutError

import discord
from discord.ext import commands

from utils import checks
from utils.l10n import get_l10n
from utils.utils import generateID


class RoleButton(discord.ui.Button['RoleView']):
    def __init__(self, label: str, emoji: str, roles: list[discord.Role], id: str, l10n):
        super().__init__(label=label, emoji=emoji, custom_id=id)
        self.l10n = l10n
        self.roles = roles

    async def callback(self, interaction: discord.Interaction):
        roles = []
        for role in self.roles:
            if role in interaction.user.roles:
                await interaction.user.remove_roles(role)
                roles.append((role.mention, 'Removed'))
            else:
                await interaction.user.add_roles(role)
                roles.append((role.mention, 'Added'))

        if len(roles) == 1:
            await interaction.response.send_message(
                content=self.l10n.format_value(
                    'role-action-success',
                    {'role': roles[0][0], 'action': roles[0][1].lower()}
                ),
                ephemeral=True
            )
        else:
            embed = discord.Embed(
                description=self.l10n.format_value(
                    'roles-action-success',
                    {'roles': '\n'.join((f'- {action} {role}' for role, action in roles))}
                ),
                color=discord.Color.blurple()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)

class RoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

class ButtonRoles(commands.Cog):
    """Self role management"""

    def __init__(self, bot):
        self.bot = bot
        self.views = {}

        with open('db/emojis.json') as f:
            self.emojis = json.load(f)['games']

        self.conn = sqlite3.connect('db/self_roles.db')
        self.c = self.conn.cursor()

        self.bot.loop.create_task(self.load_views())

    async def cog_check(self, ctx) -> bool:
        l10n = await get_l10n(
            ctx.guild.id if ctx.guild else 0,
            'self_roles',
            self.bot.conn
        )
        self.fmv = l10n.format_value
        return await checks.is_mod().predicate(ctx)

    @commands.group(name='button_role', aliases=['br'], invoke_without_command=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    async def roles(self, ctx):
        """Command group for reaction role functionality"""
        await ctx.send_help(ctx.command)

    @roles.command()
    async def add(self, ctx, name: str, message: discord.Message, roles: commands.Greedy[discord.Role]):
        """Add a button role.

        Parameters
        ------------
        `name`: <class 'str'>
            The string that will show up on the button. If this string matches \
            a game name in the database, a corresponding emoji will be used \
            automatically.

        `message`: discord.Message
            The message on which the self role button is to be added.

        `roles`: List[discord.Role]
            The list of roles given when a user reacts.
        """
        if message.author != self.bot.user:
            await ctx.reply(self.fmv('message-author-not-self'))
            return

        if not (reaction := self.emojis.get(name, None)):
            msg = await ctx.reply(self.fmv('react-message'))

            def check(reaction, user):
                return user == ctx.author and reaction.message.id == msg.id

            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                reaction = reaction.emoji
            except TimeoutError:
                await ctx.send(self.fmv('react-timeout'))
                return

        IDs = self.c.execute('select Button_ID from buttons').fetchall()
        ID = generateID(IDs)

        button = RoleButton(name, str(reaction), roles, ID, self.l10n)

        if message.id in self.views:
            try:
                self.views[message.id].add_item(button)
            except ValueError:
                await ctx.reply(self.l10n.format_value('max-limit-exceeded'))
                return
        else:
            self.views[message.id] = RoleView()
            self.views[message.id].add_item(button)
            self.c.execute(
                'insert into views values (?,?,0)',
                (message.channel.id, message.id)
            )
        self.c.execute(
            'insert into buttons values (?,?,?,?,?)',
            (ID, name, str(reaction), json.dumps([role.id for role in roles]), message.id)
        )
        self.conn.commit()

        await message.edit(view=self.views[message.id])

        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(
            name=self.l10n.format_value('react-success'),
            value=self.l10n.format_value('id', {'id': ID})
        )
        try:
            await msg.edit(content=None, embed=embed)
        except NameError:
            await ctx.send(embed=embed)

    @roles.command(aliases=['rm'])
    async def remove(self, ctx, ID: str):
        """Remove a button role.

        Parameters
        ------------
        `ID`: <class 'str'>
            The ID of the reaction to be removed.
        """
        IDs = self.c.execute(
            '''select v.Channel_ID, v.Message_ID from views v join buttons b
            on v.Message_ID = b.Message_ID where b.Button_ID = ?''', (ID,)
        ).fetchone()
        if not IDs:
            await ctx.reply(self.l10n.format_value('react-notfound', {'id': ID}))
            return
        channel = ctx.guild.get_channel(IDs[0])
        message = await channel.fetch_message(IDs[1])

        item = discord.utils.get(self.views[message.id].children, custom_id=ID)
        self.views[message.id].remove_item(item)

        self.c.execute('pragma foreign_keys = ON')

        if not self.views[message.id].children:
            await message.edit(view=None)
            del self.views[message.id]
            self.c.execute('delete from views where Message_ID = ?', (message.id,))
        else:
            await message.edit(view=self.views[message.id])
            self.c.execute('delete from buttons where Button_ID = ?', (ID,))
        self.conn.commit()

        await ctx.reply(self.l10n.format_value('remove-success', {'id': ID}))

    async def load_views(self):
        views = self.c.execute(
            'select Channel_ID, Message_ID from views'
        ).fetchall()

        for view in views:
            self.views[view[1]] = RoleView()
            channel = self.bot.get_channel(view[0])
            l10n = get_l10n(channel.guild.id if channel.guild else 0, 'self_roles')

            buttons = self.c.execute(
                '''select Button_ID, Label, Emoji, Role_IDs
                    from buttons where Message_ID = ?
                ''', (view[1],)
            ).fetchall()
            for button in buttons:
                roles = []
                for role_ID in json.loads(button[3]):
                    roles.append(channel.guild.get_role(role_ID))
                ui_button = RoleButton(button[1], button[2], roles, button[0], l10n)
                self.views[view[1]].add_item(ui_button)

            message = await channel.fetch_message(view[1])
            await message.edit(view=self.views[view[1]])

class ReactionRoles(commands.Cog):
    """Reaction role management"""

    def __init__(self, bot):
        self.bot = bot

        with open('db/self_roles.json') as f:
            self.reactions = json.load(f)
        with open('db/emojis.json') as f:
            self.emojis = json.load(f)['games']

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Called when a reaction is added to a message"""
        if not (details := self.reactions.get(str(payload.guild_id))):
            return

        flag = False
        for reaction_role in details:
            if payload.emoji.is_unicode_emoji():
                emoji = str(payload.emoji)
            else:
                emoji = payload.emoji.id
            if (payload.message_id, emoji) == (reaction_role['message_id'], reaction_role['emoji']):
                flag = True
                break
        if not flag:
            return

        guild = self.bot.get_guild(payload.guild_id)
        role = guild.get_role(reaction_role['role_id'])
        if role:
            await payload.member.add_roles(role)
        else:
            self.reactions[str(payload.guild_id)].remove(reaction_role)
            self.save()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        """Called when a reaction is removed from a message"""
        if not (details := self.reactions.get(str(payload.guild_id))):
            return

        flag = False
        for reaction_role in details:
            if payload.emoji.is_unicode_emoji():
                emoji = str(payload.emoji)
            else:
                emoji = payload.emoji.id
            if (payload.message_id, emoji) == (reaction_role['message_id'], reaction_role['emoji']):
                flag = True
                break
        if not flag:
            return

        guild = self.bot.get_guild(payload.guild_id)
        member = guild.get_member(payload.user_id)
        role = guild.get_role(reaction_role['role_id'])
        if role:
            await member.remove_roles(role)
        else:
            self.reactions[str(payload.guild_id)].remove(reaction_role)
            self.save()

    async def cog_check(self, ctx) -> bool:
        self.l10n = get_l10n(ctx.guild.id if ctx.guild else 0, 'self_roles')
        return await checks.is_mod().predicate(ctx)

    @commands.group(name='reaction_role', aliases=['rr'], invoke_without_command=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    async def roles(self, ctx):
        """Command group for reaction role functionality"""
        await ctx.send_help(ctx.command)

    @roles.command()
    async def add(self, ctx, message: discord.Message, role: discord.Role, *, game: str=None):
        """Add a reaction role.

        Parameters
        ------------
        `message`: discord.Message
            The message on which reactions will be captured.

        `role`: discord.Role
            The role given when a user reacts.

        `game`: Optional[<class 'str'>]
            If inputted, this checks for a corresponding emoji in the memory to \
            be added directly as a reaction. If left blank, the user is prompted \
            to select a reaction emoji manually.
        """
        if game:
            if not (reaction := self.emojis.get(game, None)):
                await ctx.reply(self.l10n.format_value('invalid-game', {'game': game}))
                return
        else:
            msg = await ctx.reply(self.l10n.format_value('react-message'))

            def check(reaction, user):
                return user == ctx.author and reaction.message.id == msg.id

            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                reaction = reaction.emoji
            except TimeoutError:
                await ctx.send(self.l10n.format_value('react-timeout'))
                return
        await message.add_reaction(reaction)

        if not self.reactions.get(str(ctx.guild.id)):
            self.reactions[str(ctx.guild.id)] = []
        ID = generateID([item['ID'] for item in self.reactions[str(ctx.guild.id)]])

        if isinstance(reaction, str):
            if reaction[0] == '<':
                reaction = int(reaction.split(':')[2][:-1])
        else:
            reaction = reaction.id

        item = {
            'ID': ID,
            'emoji': reaction,
            'role_id': role.id,
            'type': 1,
            'message_id': message.id,
            'channel_id': message.channel.id
        }
        self.reactions[str(ctx.guild.id)].append(item)
        self.save()

        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(
            name=self.l10n.format_value('react-success'),
            value=self.l10n.format_value('id', {'id': ID})
        )

        if game:
            await ctx.reply(embed=embed)
        else:
            await msg.edit(content=None, embed=embed)

    @roles.command(aliases=['rm'])
    async def remove(self, ctx, ID: str):
        """Remove a reaction role.

        Parameters
        ------------
        `ID`: <class 'str'>
            The ID of the reaction to be removed.
        """
        if not (details := self.reactions.get(str(ctx.guild.id))):
            return

        for reaction_role in self.reactions[str(ctx.guild.id)]:
            if ID == reaction_role['ID']:
                channel = self.bot.get_channel(reaction_role['channel_id'])
                message = await channel.fetch_message(reaction_role['message_id'])

                if isinstance(emoji := reaction_role['emoji'], int):
                    for game in self.emojis:
                        if str(emoji) in self.emojis[game]:
                            emoji = self.emojis[game]
                            break

                await message.remove_reaction(emoji, self.bot.user)
                self.reactions[str(ctx.guild.id)].remove(reaction_role)
                self.save()

                await ctx.reply(self.l10n.format_value('remove-success', {'id': ID}))
                return

        await ctx.reply(self.l10n.format_value('react-notfound', {'id': ID}))

    def save(self):
        """Save the data to a json file"""
        with open('db/self_roles.json', 'w') as f:
            json.dump(self.reactions, f)

def setup(bot):
    """Called when this file is attempted to be loaded as an extension"""
    bot.add_cog(ButtonRoles(bot))
    bot.add_cog(ReactionRoles(bot))
