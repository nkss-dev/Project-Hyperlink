import json
import sqlite3
from asyncio import TimeoutError

import discord
from discord.ext import commands

from utils.utils import generateID


class RoleButton(discord.ui.Button['RoleView']):
    def __init__(self, label: str, emoji: str, role: discord.Role, id: str, l10n):
        super().__init__(
            label=f'{label} │ {len(role.members)}', emoji=emoji, custom_id=id
        )
        self.l10n = l10n
        self.role = role

    async def callback(self, interaction: discord.Interaction):
        if self.role in interaction.user.roles:
            await interaction.user.remove_roles(self.role)
            action = 'Removed'
        else:
            await interaction.user.add_roles(self.role)
            action = 'Added'

        await interaction.response.send_message(
            content=self.l10n.format_value(
                'role-action-success',
                {'role': self.role.mention, 'action': action.lower()}
            ),
            ephemeral=True
        )
        self.label = f"{self.label.split(' │ ')[0]} │ {len(self.role.members)}"
        await interaction.message.edit(view=self.view)

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
        l10n = await self.bot.get_l10n(ctx.guild.id if ctx.guild else 0)
        self.fmv = l10n.format_value
        # TODO: Add `is_mod`
        return super().cog_check(ctx)

    @commands.group(name='button_role', aliases=['br'], invoke_without_command=True)
    @commands.bot_has_permissions(manage_roles=True)
    @commands.has_permissions(manage_roles=True)
    @commands.guild_only()
    async def roles(self, ctx):
        """Command group for reaction role functionality"""
        await ctx.send_help(ctx.command)

    @roles.command()
    async def add(self, ctx, name: str, message: discord.Message, role: discord.Role):
        """Add a button role.

        Parameters
        ------------
        `name`: <class 'str'>
            The string that will show up on the button. If this string matches \
            a game name in the database, a corresponding emoji will be used \
            automatically.

        `message`: discord.Message
            The message on which the self role button is to be added.

        `role`: discord.Role
            The role added/removed when a user clicks the button.
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

        IDs = self.c.execute('SELECT id FROM button').fetchall()
        ID = generateID(IDs)

        button = RoleButton(name, str(reaction), role, ID, self.l10n)

        if message.id in self.views:
            try:
                self.views[message.id].add_item(button)
            except ValueError:
                await ctx.reply(self.fmv('max-limit-exceeded'))
                return
        else:
            self.views[message.id] = RoleView()
            self.views[message.id].add_item(button)
            self.c.execute(
                'INSERT INTO view VALUES (?,?,0)',
                (message.channel.id, message.id)
            )
        self.c.execute(
            'INSERT INTO button VALUES (?,?,?,?,?)',
            (ID, name, str(reaction), role.id, message.id)
        )
        self.conn.commit()

        await message.edit(view=self.views[message.id])

        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(
            name=self.fmv('react-success'),
            value=self.fmv('id', {'id': ID})
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
            '''
            SELECT
                channel_id,
                message_id
            FROM
                view v
                NATURAL JOIN button
            WHERE
                button.id = ?
            ''', (ID,)
        ).fetchone()
        if not IDs:
            await ctx.reply(self.fmv('react-notfound', {'id': ID}))
            return
        channel = ctx.guild.get_channel(IDs[0])
        message = await channel.fetch_message(IDs[1])

        item = discord.utils.get(self.views[message.id].children, custom_id=ID)
        self.views[message.id].remove_item(item)

        self.c.execute('pragma foreign_keys = ON')

        if not self.views[message.id].children:
            await message.edit(view=None)
            del self.views[message.id]
            self.c.execute('DELETE FROM view WHERE message_id = ?', (message.id,))
        else:
            await message.edit(view=self.views[message.id])
            self.c.execute('DELETE FROM button WHERE id = ?', (ID,))
        self.conn.commit()

        await ctx.reply(self.fmv('remove-success', {'id': ID}))

    async def load_views(self):
        # TODO: Fix code
        await self.bot.wait_until_ready()

        views = self.c.execute(
            'SELECT channel_id, message_id FROM view'
        ).fetchall()

        for view in views:
            self.views[view[1]] = RoleView()
            channel = self.bot.get_channel(view[0])
            if not channel:
                self.bot.logger.warning(
                    f"Channel id `{view[0]}` not found in table `view`"
                )
                continue
            l10n = await self.bot.get_l10n(channel.guild.id if channel.guild else 0)

            buttons = self.c.execute(
                '''
                SELECT
                    id,
                    label,
                    emoji,
                    role_id
                FROM
                    button
                WHERE
                    message_id = ?
                ORDER BY
                    label
                ''', (view[1],)
            ).fetchall()
            for id, label, emoji, role_id in buttons:
                role = channel.guild.get_role(role_id)
                ui_button = RoleButton(label, emoji, role, id, l10n)
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
        l10n = await self.bot.get_l10n(ctx.guild.id if ctx.guild else 0)
        self.fmv = l10n.format_value
        # TODO: Add `is_mod`
        return super().cog_check(ctx)

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
                await ctx.reply(self.fmv('invalid-game', {'game': game}))
                return
        else:
            msg = await ctx.reply(self.fmv('react-message'))

            def check(reaction, user):
                return user == ctx.author and reaction.message.id == msg.id

            try:
                reaction, _ = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                reaction = reaction.emoji
            except TimeoutError:
                await ctx.send(self.fmv('react-timeout'))
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
            name=self.fmv('react-success'),
            value=self.fmv('id', {'id': ID})
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

                await ctx.reply(self.fmv('remove-success', {'id': ID}))
                return

        await ctx.reply(self.fmv('react-notfound', {'id': ID}))

    def save(self):
        """Save the data to a json file"""
        with open('db/self_roles.json', 'w') as f:
            json.dump(self.reactions, f)

async def setup(bot):
    await bot.add_cog(ButtonRoles(bot))
    await bot.add_cog(ReactionRoles(bot))
