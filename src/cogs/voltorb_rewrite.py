import random

import discord
from discord.ext import commands

import cogs.checks as checks


class Embed(discord.Embed):
    def __init__(self, author, is_guild, level=1, coins=0, total=0):
        super().__init__(
            color=author.color if is_guild else discord.Color.blurple(),
        )

        self.set_author(name=f"{author}'s session", icon_url=author.display_avatar.url)

        self.thumb = discord.File("sprites/voltorb.gif", filename="voltorb.gif")
        self.set_thumbnail(url="attachment://voltorb.gif")

        self.add_field(name="Level:", value=level, inline=True)
        self.add_field(name="Coins:", value=coins, inline=True)
        self.add_field(name="Total Coins:", value=total, inline=True)


class GameView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)


class HiddenButton(discord.ui.Button["GameView"]):
    def __init__(self, value):
        super().__init__(label="\u200b")
        self.value = value

    async def callback(self, interaction: discord.Interaction):
        if not self.value:
            self.emoji = "<a:voltorb:914169587606626314>"
            self.style = discord.ButtonStyle.red
            self.view.add_item(DropDown())
        elif self.value in (1, 2, 3):
            self.style = discord.ButtonStyle.green

        self.label = self.value or None
        self.disabled = True

        await interaction.response.edit_message(view=self.view)


class StatsButton(discord.ui.Button["GameView"]):
    def __init__(self, count, voltorbs):
        super().__init__(
            disabled=True,
            label=f"{count}:{voltorbs}",
            style=discord.ButtonStyle.blurple,
        )


class DropDown(discord.ui.Select["GameView"]):
    def __init__(self):
        options = [discord.SelectOption(label="abc", description="Reveal all tiles")]
        super().__init__(
            placeholder="Choose an option to proceed...",
            options=options,
        )


class Game:
    """Game logic handler"""

    def __init__(self):
        self.level = 1
        self.coins = 0
        self.total = 0

        self.choices = 0, 1, 2, 3
        self.weights = {
            1: (0.35, 0.45, 0.15, 0.05),
            2: (0.35, 0.45, 0.15, 0.05),
            3: (0.35, 0.45, 0.15, 0.05),
            4: (0.35, 0.45, 0.15, 0.05),
            5: (0.35, 0.45, 0.15, 0.05),
            6: (0.35, 0.45, 0.15, 0.05),
            7: (0.35, 0.45, 0.15, 0.05),
        }
        self.dimension = 4

        self.board = self.create_board()
        self.count = self.get_count()
        for row in self.board:
            print(row)

    def create_board(self) -> list[list[int]]:
        """Create the board for the game"""
        values = random.choices(
            self.choices, self.weights[self.level], k=self.dimension**2
        )
        board = []
        for i in range(0, self.dimension**2, self.dimension):
            board.append(values[i : i + self.dimension])

        return board

    def get_count(self) -> dict[str, list[tuple[int, int]]]:
        """Get the count of the board"""
        count = {"row": [], "col": []}
        for row in self.board:
            count["row"].append((sum(row), row.count(0)))

        temp = []
        for i, _ in enumerate(self.board):
            column = [row[i] for row in self.board]
            temp.append((sum(column), column.count(0)))
        count["col"] = temp

        return count


class Voltorb(commands.Cog):
    """The Voltorb Flip game"""

    def __init__(self, bot):
        self.bot = bot
        self.games: dict[int, tuple[Game, GameView]] = {}

    async def cog_check(self, ctx):
        return checks.is_verified()

    def create_game_view(self, board, count) -> GameView:
        """Create the game view"""
        view = GameView()
        for i, row in enumerate(board):
            for value in row:
                view.add_item(HiddenButton(value))
            view.add_item(StatsButton(*count["row"][i]))
        for i, _ in enumerate(board):
            view.add_item(StatsButton(*count["col"][i]))

        return view

    @commands.group(aliases=["vf", "vf_start"], invoke_without_command=True)
    async def voltorb(self, ctx):
        """Start the game"""
        embed = Embed(ctx.author, bool(ctx.guild))

        id = ctx.author.id
        if not self.games.get(id):
            game = Game()
            view = self.create_game_view(game.board, game.count)
            self.games[id] = game, view

        await ctx.send(embed=embed, file=embed.thumb, view=self.games[id][1])


async def setup(bot):
    await bot.add_cog(Voltorb(bot))
