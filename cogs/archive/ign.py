import re
import requests
import sqlite3
from typing import Optional
from urllib.parse import quote_plus

import config
import discord
from discord.ext import commands

import cogs.checks as checks
from main import ProjectHyperlink


class Details(discord.ui.View):
    def __init__(self, l10n, user, game, id):
        super().__init__()
        self.id = id
        self.game = game
        self.l10n = l10n
        self.user = user

    async def interaction_check(self, interaction) -> bool:
        if interaction.user != self.user:
            await interaction.response.send_message(
                content=self.fmv("incorrect-user"), ephemeral=True
            )
            return False
        return True

    @discord.ui.button(label="More details")
    async def expand(self, button: discord.ui.Button, interaction: discord.Interaction):
        embed = games[self.game].parse(self.user, self.id)
        await interaction.response.edit_message(embed=embed, view=None)


class Clash_of_Clans:
    def __init__(self):
        link = "https://cdn.discordapp.com/attachments/932880404250255381"
        self.league_images = {
            "Unranked": f"{link}/932880626070220800/Unranked_League.webp",
            "Bronze": f"{link}/932880624375709746/Bronze_League.webp",
            "Silver": f"{link}/932880625646587954/Silver_League.webp",
            "Gold": f"{link}/932880625042616350/Gold_League.webp",
            "Crystal": f"{link}/932880624824508416/Crystal_League.webp",
            "Master": f"{link}/932880625411698688/Master_League.webp",
            "Champion": f"{link}/932880624547672144/Champion_League.webp",
            "Titan": f"{link}/932880625852096542/Titan_League.webp",
            "Legend": f"{link}/932880625227169833/Legend_League.webp",
        }
        self.headers = {
            "Accept": "application/json",
            "authorization": f"Bearer {config.coc_api_token}",
        }
        self.status_codes = 400, 403, 404, 429, 500, 503

        self.cache = {}

    def parse(self, member, id) -> discord.Embed:
        if self.cache.get(id):
            return self.cache[id]

        if id.startswith("#"):
            id = quote_plus(id)
        else:
            id = quote_plus(f"#{id}")

        src = requests.get(
            f"https://api.clashofclans.com/v1/players/{id}", headers=self.headers
        )
        if src.status_code in self.status_codes:
            print(src.json())
            return discord.Embed(description="Error 404: Not found")

        details = src.json()
        link = "https://link.clashofclans.com/?action="

        # Setting variables for the embed
        player = f"[Go to player profile]({link}OpenPlayerProfile&tag={id})"
        if clan := details.get("clan"):
            clan = f"[{clan['name']}]({link}OpenClanProfile&tag={clan['tag']})"
        else:
            clan = "No clan joined"
        league = f"\U0001f3c6 {details['trophies']}/{details['bestTrophies']} - {details['league']['name']}"
        townHallLevel = details["townHallLevel"]
        if subLevel := details.get("townHallWeaponLevel"):
            townHallLevel += subLevel / 10
        builderHallLevel = details["builderHallLevel"]

        if member.color == discord.Color.default():
            color = discord.Color.blurple()
        else:
            color = member.color

        embed = discord.Embed(
            title=f"{details['name']} - Level {details['expLevel']}",
            description=player,
            color=color,
        )
        embed.set_footer(text=str(member), icon_url=member.display_avatar)

        embed.add_field(
            name="Halls",
            value=f"Town hall: {townHallLevel}\nBuilder hall: {builderHallLevel}",
            inline=False,
        )
        embed.add_field(name="League", value=league, inline=False)
        embed.add_field(name="Clan", value=clan, inline=False)

        league = re.search(r"\w+ League ", details["league"]["name"]).group(0)
        embed.set_thumbnail(url=self.league_images[league.split(" ", 1)[0]])

        self.cache[id] = embed
        return embed


class Valorant:
    def __init__(self):
        link = "https://cdn.discordapp.com/attachments/932515398996357130"
        self.profile = "https://tracker.gg/valorant/profile/riot"
        self.rank_images = {
            "Unranked": f"{link}/932872767928430662/unranked.png",
            "Iron 1": f"{link}/932515684213203014/Iron_1.webp",
            "Iron 2": f"{link}/932515684460687410/Iron_2.webp",
            "Iron 3": f"{link}/932515684733321256/Iron_3.webp",
            "Bronze 1": f"{link}/932526669204422656/Bronze_1.webp",
            "Bronze 2": f"{link}/932526669409951795/Bronze_2.webp",
            "Bronze 3": f"{link}/932526669665816677/Bronze_3.webp",
            "Silver 1": f"{link}/932526702792413254/Silver_1.webp",
            "Silver 2": f"{link}/932526702985355294/Silver_2.webp",
            "Silver 3": f"{link}/932526703186702356/Silver_3.webp",
            "Gold 1": f"{link}/932526729271083038/Gold_1.webp",
            "Gold 2": f"{link}/932526729455624212/Gold_2.webp",
            "Gold 3": f"{link}/932526729669513306/Gold_3.webp",
            "Platinum 1": f"{link}/932526761030328350/Platinum_1.webp",
            "Platinum 2": f"{link}/932526761231667200/Platinum_2.webp",
            "Platinum 3": f"{link}/932526761453944902/Platinum_3.webp",
            "Diamond 1": f"{link}/932872681311834142/Diamond_1.webp",
            "Diamond 2": f"{link}/932872681513156608/Diamond_2.webp",
            "Diamond 3": f"{link}/932872681773223946/Diamond_3.webp",
            "Immortal 1": f"{link}",
            "Immortal 2": f"{link}",
            "Immortal 3": f"{link}/932872719198982144/Immortal_3.webp",
            "Radiant": f"{link}/932872741609152603/Radiant.webp",
        }

        self.cache = {}

    def parse(self, member, id) -> discord.Embed:
        if self.cache.get(id):
            return self.cache[id]

        region = "ap"
        name, tag = id.split("#")
        name, tag = quote_plus(name), quote_plus(tag)
        print(f"https://api.kyroskoh.xyz/valorant/v1/mmr/{region}/{name}/{tag}")
        src = requests.get(
            f"https://api.kyroskoh.xyz/valorant/v1/mmr/{region}/{name}/{tag}"
        )

        text = "Go to player profile"
        profile = f"[{text}]({self.profile}/{quote_plus(id)}/overview)"
        if member.color == discord.Color.default():
            color = discord.Color.blurple()
        else:
            color = member.color

        embed = discord.Embed(title=id, description=profile, color=color)
        embed.set_footer(text=str(member), icon_url=member.display_avatar)

        if src.status_code != 200:
            print(src, id)
            return discord.Embed(description="An error occured")
        else:
            rank = re.search(r"^\[\w+ \d\]", src.json()).group(0)[1:-1]
        embed.add_field(name="Rank", value=rank)
        embed.set_thumbnail(url=self.rank_images[rank])

        self.cache[id] = embed
        return embed


games = {"clash of clans": Clash_of_Clans(), "valorant": Valorant()}


class IGN(commands.Cog):
    """[deprecated] Store IGNs for games"""

    def __init__(self, bot):
        self.bot = bot
        self.games = []

    def get_IGNs(self, author_id: int) -> sqlite3.Cursor:
        """Return the IGNs of the given user"""
        cursor = self.bot.c.execute(
            "select * from ign where Discord_UID = ?", (author_id,)
        )
        return cursor

    async def exists(self, ctx, game) -> str:
        """Check if entered game exists in the database"""
        result: str = ""
        for _game in self.games:
            if game.lower() == _game[0].lower():
                result = _game[0]
                break

        if not result:
            content = self.fmv(
                "game-notfound",
                {"game": game, "cmd": f"{ctx.clean_prefix}{ctx.command.parent}"},
            )
            await ctx.reply(content)
        return result

    async def cog_check(self, ctx: commands.Context[ProjectHyperlink]) -> bool:
        l10n = await self.bot.get_l10n(ctx.guild.id if ctx.guild else 0)
        self.fmv = l10n.format_value
        return await checks._is_verified(ctx)

    @commands.group()
    async def ign(self, ctx):
        """Show the list of eligible games for which an IGN can be added.

        This is also the parent command to perform any read/write operations \
        to any of the user's IGNs.
        """
        self.games = self.bot.c.execute(
            "select * from ign where Discord_UID = null"
        ).description[1:]
        if not self.games:
            await ctx.reply(self.fmv("game-list-notfound"))
            return

        if ctx.invoked_subcommand:
            return

        embed = discord.Embed(
            title=self.fmv("game-list"),
            description="\n".join([game[0] for game in self.games]),
            color=discord.Color.blurple(),
        )
        await ctx.send(embed=embed)

    @ign.command()
    async def add(self, ctx, game: str, ign: str):
        """Add an IGN for the given game.

        Parameters
        ------------
        `game`: <class 'str'>
            The game for which an IGN is to be stored. It is case insensitive \
            and can only contain a game that is stored in the memory \
            (``games.json``).
            Available games can be checked via the `ign` command.

        `ign`: <class 'str'>
            The IGN for the specified game. This can be anything as long as \
            it is a string (yes, a link too). However, this cannot contain \
            tags like user/role mentions or `@everyone` and `@here`.
        """
        if not (game := await self.exists(ctx, game)):
            return

        if ctx.message.mentions:
            await ctx.reply(self.fmv("mentions-not-allowed"))
            return

        exists = self.get_IGNs(ctx.author.id).fetchone()
        if not exists:
            self.bot.c.execute(
                f"insert into ign (Discord_UID, {game}) values(?,?)",
                (
                    ctx.author.id,
                    ign,
                ),
            )
        else:
            self.bot.c.execute(
                f"update ign set {game} = ? where Discord_UID = ?",
                (
                    ign,
                    ctx.author.id,
                ),
            )
        self.bot.db.commit()

        await ctx.reply(self.fmv("add-success", {"game": game}))

    @ign.command()
    async def show(self, ctx, user: Optional[discord.Member], *, game: str = None):
        """Show the IGN(s) of a user.

        Displays one or all IGNs of the author of the command or of the \
        specified user. Please note that if the specified user was not found, \
        it will be added to the `game` parameter.

        Parameters
        ------------
        `user`: Optional[discord.Member]
            The name/ID/tag of a user. If specified, the IGNs returned will \
            be of the user instead of the author of the command.

        `game`: Optional[<class 'str'>]
            The name of the game for which an IGN needs to be displayed.
            Displays all the stored IGNs if not specified.
        """
        member = user or ctx.author
        oneself = ctx.author == member
        if ctx.guild:
            color = member.color
        else:
            color = discord.Color.blurple()

        cursor = self.get_IGNs(member.id)
        if not (igns := cursor.fetchone()):
            if oneself:
                await ctx.reply(
                    self.fmv(
                        "self-igns-notfound",
                        {"cmd": ctx.clean_prefix + ctx.command.parent.name},
                    )
                )
            else:
                embed = discord.Embed(
                    description=self.fmv(
                        "other-igns-notfound", {"member": member.mention}
                    ),
                    color=color,
                )
                await ctx.reply(embed=embed)
            return

        if game:
            try:
                ign = self.bot.c.execute(
                    f"select `{game}` from ign where Discord_UID = ?", (member.id,)
                ).fetchone()
            except sqlite3.OperationalError:
                content = self.fmv(
                    "game-notfound",
                    {"game": game, "cmd": f"{ctx.clean_prefix}{ctx.command.parent}"},
                )
                await ctx.reply(content)
                return
            if ign:
                embed = discord.Embed(description=ign, color=color)
                if games.get(game.lower()):
                    view = Details(self.l10n, ctx.author, game.lower(), ign)
                else:
                    view = None
                await ctx.send(embed=embed, view=view)
            elif oneself:
                await ctx.reply(self.fmv("self-ign-notfound", {"game": game}))
            else:
                embed = discord.Embed(
                    description=self.fmv(
                        "other-ign-notfound", {"member": member.mention, "game": game}
                    ),
                    color=color,
                )
                await ctx.reply(embed=embed)
            return

        user_igns = []
        for game, ign in zip(cursor.description[1:], igns[1:]):
            if ign:
                user_igns.append(f"**{game[0]}:** {ign}")

        embed = discord.Embed(
            title=self.fmv("igns-title", {"member": f"{member}"}),
            description="\n".join(user_igns),
            color=color,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        if not oneself:
            embed.set_footer(
                text=self.fmv("request", {"author": f"{ctx.author}"}),
                icon_url=ctx.author.avatar.url,
            )

        await ctx.send(embed=embed)

    @ign.command(aliases=["del", "remove", "rm"])
    async def delete(self, ctx, *, game: str = None):
        """Delete an IGN for the given game or all games.

        Parameters
        ------------
        `game`: Optional[<class 'str'>]
            The game for which an IGN is to be deleted. It is case \
            insensitive and can only contain a game that has a corresponding \
            IGN for the user.
            If this is left blank, all the stored IGNs are deleted.
        """
        cursor = self.get_IGNs(ctx.author.id)
        if not (igns := cursor.fetchone()):
            await ctx.reply(
                self.fmv(
                    "self-igns-notfound",
                    {"cmd": f"{ctx.clean_prefix}{ctx.command.parent}"},
                )
            )
            return

        if not game:
            self.bot.c.execute(
                "delete from ign where Discord_UID = ?", (ctx.author.id,)
            )
            self.bot.db.commit()
            await ctx.reply(self.fmv("remove-all-success"))
            return

        if not (game := await self.exists(ctx, game)):
            return

        ign = self.bot.c.execute(
            f"select `{game}` from ign where Discord_UID = ?", (ctx.author.id,)
        ).fetchone()
        if ign:
            igns = [ign for ign in igns[1:] if ign]
            if len(igns) > 1:
                self.bot.c.execute(
                    f"update ign set `{game}` = null where Discord_UID = ?",
                    (ctx.author.id,),
                )
            else:
                self.bot.c.execute(
                    "delete from ign where Discord_UID = ?", (ctx.author.id,)
                )
            self.bot.db.commit()
            await ctx.reply(self.fmv("remove-success", {"game": game}))
        else:
            await ctx.reply(self.fmv("self-ign-notfound", {"game": game}))

    @ign.command(name="for")
    async def igns(self, ctx, *, game: str = None):
        if not (game := await self.exists(ctx, game)):
            return

        igns = self.bot.c.execute(
            f"""select main.Discord_UID, ign.`{game}` from ign
            join main on main.Discord_UID = ign.Discord_UID
            where ign.`{game}` not null"""
        ).fetchall()
        if not igns:
            await ctx.reply(self.fmv("ign-notfound", {"game": game}))

        formatted_igns = []
        for id, ign in igns:
            if member := ctx.guild.get_member(id):
                formatted_igns.append(f"{member.mention}: {ign}")

        embed = discord.Embed(
            title=self.fmv("igns-for", {"game": game}),
            description="\n".join(formatted_igns),
            color=discord.Color.blurple(),
        )
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(IGN(bot))
