import json

from discord import Embed, File
from discord.ext import commands

from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

from random import choice

prefix = "%"
row = ["a", "b", "c", "d", "e"]
col = [1, 2, 3, 4, 5]


class voltorb_embed:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    async def run(self, ctx):
        self.vol = voltorb_board(self.vol, f"boards/{ctx.author.id}.png")
        thumb = File("sprites/voltorb.gif", filename="voltorb.gif")
        board = File(f"boards/{ctx.author.id}.png", filename="board.png")
        embed = Embed(title="Voltorb Flip", colour=ctx.author.top_role.color)
        embed.set_author(
            name=str(ctx.author) + "'s session", icon_url=ctx.author.avatar.url
        )
        embed.set_thumbnail(url="attachment://voltorb.gif")
        embed.set_image(url="attachment://board.png")
        embed.add_field(name="Level:", value=str(self.level), inline=True)
        embed.add_field(name="Coins:", value=str(self.coins), inline=True)
        embed.add_field(name="Total Coins:", value=str(self.total), inline=True)
        await ctx.message.delete()
        self.message = (await ctx.send(files=[thumb, board], embed=embed)).id

    async def flip(self, ctx):
        self.vol = voltorb_board(self.vol, f"boards/{ctx.author.id}.png")
        try:
            key = ctx.message.content.split("flip ")[1]
        except IndexError:
            await ctx.send("Type something after the command")
            return
        if "row" in key[:3].lower() or "col" in key[:3].lower():
            coins = self.vol.edit_all(
                f"boards/{ctx.author.id}.png", key[:3].lower(), key[4:].lower()
            )
        else:
            if not key[1].isdigit():
                await ctx.send(
                    f"The column parameter must be of an integer type, {ctx.author.mention}"
                )
                return
            if key[0] not in row or int(key[1]) not in col:
                await ctx.message.delete()
                bruh = await ctx.send("That's an invalid tile")
                await bruh.delete(delay=5)
                return
            coins = self.vol.edit(f"boards/{ctx.author.id}.png", key)
        try:
            int(coins)
            if coins == -1:
                self.lose = True
            elif self.coins == 0:
                self.coins = coins
            elif not coins:
                await ctx.send("The tile(s) is/are already flipped!")
                return
            else:
                self.coins *= coins
        except ValueError:
            self.win = True
            self.total += self.coins * int(coins[:-1])
        thumb = File("sprites/voltorb.gif", filename="voltorb.gif")
        board = File(f"boards/{ctx.author.id}.png", filename="board.png")
        embed = Embed(title="Voltorb Flip", colour=ctx.author.top_role.color)
        embed.set_author(
            name=str(ctx.author) + "'s session", icon_url=ctx.author.avatar.url
        )
        embed.set_thumbnail(url="attachment://voltorb.gif")
        embed.set_image(url="attachment://board.png")
        embed.add_field(name="Level:", value=str(self.level), inline=True)
        embed.add_field(name="Coins:", value=str(self.coins), inline=True)
        embed.add_field(name="Total Coins:", value=str(self.total), inline=True)
        await ctx.message.delete()
        await (await ctx.fetch_message(self.message)).delete()
        self.message = (await ctx.send(files=[thumb, board], embed=embed)).id
        if self.lose:
            self.rip = (
                await ctx.send(
                    f"Oh no! You hit a voltorb, {ctx.author.mention} and got 0 coins!\nType `{prefix}vf resume` to continue."
                )
            ).id
        if self.win:
            self.rip = (
                await ctx.send(
                    f"Game clear, {ctx.author.mention}! You received {self.coins*int(coins[:-1])} Coins! Type `{prefix}vf advance` to advance to level {self.level + 1}"
                )
            ).id
            self.coins = 0

    async def resume(self, ctx):
        try:
            await (await ctx.fetch_message(self.rip)).delete()
            self.rip = 0
            if self.level != 1:
                self.level -= 1
            self.coins = 0
            await (await ctx.fetch_message(self.message)).delete()
            await self.run(ctx)
            self.lose = False
        except TypeError:
            await ctx.send(
                f"You didn't lose your current match yet, {ctx.author.mention}. If you would like to restart, type `{prefix}restart`"
            )

    async def advance(self, ctx):
        await (await ctx.fetch_message(self.rip)).delete()
        self.rip = 0
        self.level += 1
        await (await ctx.fetch_message(self.message)).delete()
        await self.run(ctx)
        self.win = False


class voltorb_board:
    def __init__(self, dictionary, name):
        for key in dictionary:
            setattr(self, key, dictionary[key])

        if self.board:
            return

        ch = "000000111111112223"

        for i in range(5):
            self.board.append([int(choice(ch)) for _ in range(5)])

        bg = Image.open("sprites/board.png")
        font = ImageFont.truetype("arial.ttf", 120)

        for i, j in zip(range(10, 1811, 360), range(5)):
            draw = ImageDraw.Draw(bg)
            sum_num = 0
            vol_num = 0
            for k in range(5):
                if self.board[k][j] == 0:
                    vol_num += 1
                else:
                    sum_num += self.board[k][j]
            if sum_num > 9:
                x = 180
            else:
                x = 240
            draw.text((i + x, 1830), str(sum_num), (0, 0, 0), font=font)
            draw.text((i + 240, 1990), str(vol_num), (0, 0, 0), font=font)

            if sum(self.board[j]) > 9:
                x = 180
            else:
                x = 240
            draw.text((1810 + x, i + 20), str(sum(self.board[j])), (0, 0, 0), font=font)
            draw.text(
                (2050, i + 180), str(self.board[j].count(0)), (0, 0, 0), font=font
            )
        bg.save(name)

    def edit(self, name, temp):
        bg = Image.open(name)
        tile_1 = Image.open("sprites/number_tile_1.png")
        tile_2 = Image.open("sprites/number_tile_2.png")
        tile_3 = Image.open("sprites/number_tile_3.png")
        hl_voltorb_tile = Image.open("sprites/hl_voltorb_tile.png")
        pos = [temp[0], int(temp[1])]
        pos[0] = ord(pos[0].upper()) - 64
        if not self.flip[pos[0] - 1][pos[1] - 1]:
            if self.board[pos[0] - 1][pos[1] - 1] == 0:
                bg.paste(hl_voltorb_tile, (pos[1] * 360 - 350, pos[0] * 360 - 350))
                self.flip[pos[0] - 1][pos[1] - 1] = True
                bg.save(name)
                self.flip_all(name)
                return -1
            elif self.board[pos[0] - 1][pos[1] - 1] == 1:
                bg.paste(tile_1, (pos[1] * 360 - 350, pos[0] * 360 - 350))
            elif self.board[pos[0] - 1][pos[1] - 1] == 2:
                bg.paste(tile_2, (pos[1] * 360 - 350, pos[0] * 360 - 350))
            elif self.board[pos[0] - 1][pos[1] - 1] == 3:
                bg.paste(tile_3, (pos[1] * 360 - 350, pos[0] * 360 - 350))
            self.flip[pos[0] - 1][pos[1] - 1] = True

            flag = False
            for i in range(5):
                for j in range(5):
                    if self.board[i][j] > 1 and not self.flip[i][j]:
                        flag = True
            bg.save(name)
            if not flag:
                return f"{self.board[pos[0] - 1][pos[1] - 1]}x"
            return self.board[pos[0] - 1][pos[1] - 1]
        return 0

    def edit_all(self, name, rowcol, num):
        bg = Image.open(name)
        voltorb_tile = Image.open("sprites/voltorb_tile.png")
        tile_1 = Image.open("sprites/number_tile_1.png")
        tile_2 = Image.open("sprites/number_tile_2.png")
        tile_3 = Image.open("sprites/number_tile_3.png")
        hl_voltorb_tile = Image.open("sprites/hl_voltorb_tile.png")
        coins = 1
        if rowcol == "row":
            num = ord(num.upper()) - 64
            for i in range(5):
                if not self.flip[num - 1][i]:
                    if self.board[num - 1][i] == 0:
                        bg.paste(
                            hl_voltorb_tile, ((i + 1) * 360 - 350, num * 360 - 350)
                        )
                        self.flip[num - 1][i] = True
                        bg.save(name)
                        self.flip_all(name)
                        return -1
                    elif self.board[num - 1][i] == 1:
                        bg.paste(tile_1, ((i + 1) * 360 - 350, num * 360 - 350))
                    elif self.board[num - 1][i] == 2:
                        bg.paste(tile_2, ((i + 1) * 360 - 350, num * 360 - 350))
                        coins *= 2
                    elif self.board[num - 1][i] == 3:
                        bg.paste(tile_3, ((i + 1) * 360 - 350, num * 360 - 350))
                        coins *= 3
                    self.flip[num - 1][i] = True

            flag = False
            for i in range(5):
                for j in range(5):
                    if self.board[i][j] > 1 and not self.flip[i][j]:
                        flag = True
            bg.save(name)
            if not flag:
                return f"{coins}x"
            return coins
        num = int(num)
        for i in range(5):
            if self.board[i][num - 1] == 0:
                bg.paste(hl_voltorb_tile, (num * 360 - 350, (i + 1) * 360 - 350))
                self.flip[i][num - 1] = True
                bg.save(name)
                self.flip_all(name)
                return -1
            elif self.board[i][num - 1] == 1:
                bg.paste(tile_1, (num * 360 - 350, (i + 1) * 360 - 350))
            elif self.board[i][num - 1] == 2:
                bg.paste(tile_2, (num * 360 - 350, (i + 1) * 360 - 350))
                coins *= 2
            elif self.board[i][num - 1] == 3:
                bg.paste(tile_3, (num * 360 - 350, (i + 1) * 360 - 350))
                coins *= 3
            self.flip[i][num - 1] = True

        flag = False
        for i in range(5):
            for j in range(5):
                if self.board[i][j] > 1 and not self.flip[i][j]:
                    flag = True
        bg.save(name)
        if not flag:
            return f"{coins}x"
        return coins

    def flip_all(self, name):
        bg = Image.open(name)
        tile_1 = Image.open("sprites/number_tile_1.png")
        tile_2 = Image.open("sprites/number_tile_2.png")
        tile_3 = Image.open("sprites/number_tile_3.png")
        voltorb_tile = Image.open("sprites/voltorb_tile.png")
        for i in range(5):
            for j in range(5):
                if self.flip[i][j]:
                    continue
                if self.board[i][j] == 0:
                    bg.paste(voltorb_tile, ((j + 1) * 360 - 350, (i + 1) * 360 - 350))
                elif self.board[i][j] == 1:
                    bg.paste(tile_1, ((j + 1) * 360 - 350, (i + 1) * 360 - 350))
                elif self.board[i][j] == 2:
                    bg.paste(tile_2, ((j + 1) * 360 - 350, (i + 1) * 360 - 350))
                elif self.board[i][j] == 3:
                    bg.paste(tile_3, ((j + 1) * 360 - 350, (i + 1) * 360 - 350))
                self.flip[i][j] = True
        bg.save(name)


class VoltorbFlip(commands.Cog):
    """Voltorb Flip game"""

    def __init__(self, bot):
        self.bot = bot

        with open("db/boards.json") as f:
            self.data = json.load(f)

        self.dict = {
            "level": 1,
            "coins": 0,
            "total": 0,
            "lose": False,
            "win": False,
            "rip": int(),
            "message": int(),
            "vol": {
                "board": list(),
                "flip": [[False, False, False, False, False] for _ in range(5)],
            },
        }

    async def cog_check(self, ctx):
        return self.bot.verificationCheck(ctx)

    @commands.group(aliases=["vf", "vf_start"], invoke_without_command=True)
    async def voltorb_start(self, ctx):
        """This is a recreatation of the Voltorb Flip game that appears in the Korean and Western releases of Pokémon HeartGold and SoulSilver. The game is a mix between Minesweeper and Picture Cross and the placement of the bombs are given for each row and column. The goal of the game is to uncover all of the 2 and 3 tiles on a given board and move up to higher levels which have higher coin totals.

        The numbers on the side and bottom of the game board denote the sum of the tiles and how many bombs are present in that row/column, respectively. Each tile you flip multiplies your collected coins by that value. Once you uncover all of the 2 and 3 tiles, all of the coins you gained this level will be added to your total and you'll go up one level to a max of 7. If you flip over a Voltorb, you lose all your coins from the current level and risk going down to a lower level."""

        self.v1 = self.load(ctx.author.id)
        await self.v1.run(ctx=ctx)
        self.save(ctx.author.id)

    @voltorb_start.command(aliases=["f"])
    async def flip(self, ctx):
        self.v1 = self.load(ctx.author.id)
        if self.v1.win:
            await ctx.send(
                f"You've already won your current session, {ctx.author.mention}. Type `{prefix}advance` to proceed to the next level"
            )
            return
        elif self.v1.lose:
            await ctx.send(
                f"You've lost your current session, {ctx.author.mention}. Type `{prefix}resume` to continue"
            )
            return
        await self.v1.flip(ctx=ctx)
        self.save(ctx.author.id)

    @voltorb_start.command(aliases=["r"])
    async def resume(self, ctx):
        self.v1 = self.load(ctx.author.id)
        if self.v1.win:
            await ctx.send(
                f"You've already won your current session, {ctx.author.mention}. Type `{prefix}advance` to proceed to the next level"
            )
            return
        if not self.v1.lose:
            await ctx.send(
                f"You've not lost your current session yet, {ctx.author.mention}."
            )
            return
        self.v1.vol = voltorb_board(
            self.data[str(ctx.author.id)]["vol"], f"boards/{ctx.author.id}.png"
        )
        await self.v1.resume(ctx=ctx)
        self.save(ctx.author.id)

    @voltorb_start.command(aliases=["a"])
    async def advance(self, ctx):
        self.v1 = self.load(ctx.author.id)
        if self.v1.win:
            self.v1.vol = voltorb_board(
                self.data[str(ctx.author.id)]["vol"], f"boards/{ctx.author.id}.png"
            )
            await self.v1.advance(ctx=ctx)
            self.v1.win = False
            self.save(ctx.author.id)
        elif self.v1.lose:
            await ctx.send(
                f"You've lost your current session, {ctx.author.mention}. Type `{prefix}resume` to continue"
            )
            return
        else:
            await ctx.send(
                f"You didn't win your current match yet, {ctx.author.mention}. If you would like to restart, type `{prefix}restart`"
            )

    @voltorb_start.command(aliases=["q"])
    async def quit(self, ctx):
        if str(ctx.author.id) not in self.data:
            await ctx.send(
                f"You didn't start playing, {ctx.author.mention}. Type `{prefix}vf_start` to get started."
            )
            return
        self.v1 = self.load(ctx.author.id)
        await (await ctx.fetch_message(self.v1.message)).delete()
        if self.v1.rip:
            await (await ctx.fetch_message(self.v1.rip)).delete()
        self.data.pop(str(ctx.author.id))
        with open("db/boards.json", "w") as f:
            json.dump(self.data, f)
        await ctx.message.delete()

    def load(self, id):
        self.dict["name"] = id
        id = str(id)
        if id not in self.data:
            return voltorb_embed(self.dict)
        return voltorb_embed(self.data[id])

    def save(self, id):
        id = str(id)
        try:
            del self.data[id]
        except KeyError:
            pass
        self.data[id] = self.v1.__dict__
        self.data[id]["vol"] = self.data[id]["vol"].__dict__
        # del self.data[id]['vol']
        with open("db/boards.json", "w") as f:
            json.dump(self.data, f)


async def setup(bot):
    await bot.add_cog(VoltorbFlip(bot))
