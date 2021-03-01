import random, os
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

class voltorb:
    def __init__(self):

        self.board = []
        self.flip = []
        ch = '000000111111112223'

        for i in range(5):
            self.board.append([int(random.choice(ch)) for j in range(5)])
            self.flip.append([False, False, False, False, False])

        sq1 = Image.new('RGBA', (100, 100), color=(20, 132, 92))
        sq2 = Image.new('RGBA', (100, 100), color=(44, 164, 100))

        vline = Image.new('RGBA', (10, 350), color=(0, 0, 0))
        hline = Image.new('RGBA', (350, 10), color=(0, 0, 0))

        self.font = ImageFont.truetype('arial.ttf', 120)

        self.square = Image.new('RGBA', (350, 350), color=(20, 132, 92))
        self.square.paste(vline, (0, 0))
        self.square.paste(vline, (340, 0))
        self.square.paste(hline, (0, 0))
        self.square.paste(hline, (0, 340))
        self.square.paste(sq2, (125, 25))
        self.square.paste(sq2, (25, 125))
        self.square.paste(sq2, (225, 125))
        self.square.paste(sq2, (125, 225))

        self.voltorb_row = [Image.new('RGBA', (350, 350), color=(222, 112, 85)),
                Image.new('RGBA', (350, 350), color=(69, 167, 70)),
                Image.new('RGBA', (350, 350), color=(230, 159, 67)),
                Image.new('RGBA', (350, 350), color=(55, 146, 245)),
                Image.new('RGBA', (350, 350), color=(191, 101, 221))]

        self.voltorb_col = [Image.new('RGBA', (350, 350), color=(222, 112, 85)),
                Image.new('RGBA', (350, 350), color=(69, 167, 70)),
                Image.new('RGBA', (350, 350), color=(230, 159, 67)),
                Image.new('RGBA', (350, 350), color=(55, 146, 245)),
                Image.new('RGBA', (350, 350), color=(191, 101, 221))]

        voltorb_png = Image.open('voltorb 160.png')

        for i, j in zip(range(10, 1811, 360), range(5)):
            self.voltorb_row[j].paste(vline, (0, 0))
            self.voltorb_row[j].paste(vline, (340, 0))
            self.voltorb_row[j].paste(hline, (0, 0))
            self.voltorb_row[j].paste(hline, (0, 340))
            self.voltorb_row[j].paste(hline, (0, 150))
            self.voltorb_row[j].alpha_composite(voltorb_png, (20, 170))
            self.voltorb_col[j].paste(vline, (0, 0))
            self.voltorb_col[j].paste(vline, (340, 0))
            self.voltorb_col[j].paste(hline, (0, 0))
            self.voltorb_col[j].paste(hline, (0, 340))
            self.voltorb_col[j].paste(hline, (0, 150))
            self.voltorb_col[j].alpha_composite(voltorb_png, (20, 170))
            draw = ImageDraw.Draw(self.voltorb_row[j])
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
            draw.text((x, 20), str(sum_num), (0, 0, 0), font=self.font)
            draw.text((240, 180), str(vol_num), (0, 0, 0), font=self.font)

            draw = ImageDraw.Draw(self.voltorb_col[j])
            if sum(self.board[j]) > 9:
                x = 180
            else:
                x = 240
            draw.text((x, 20), str(sum(self.board[j])), (0, 0, 0), font=self.font)
            draw.text((240, 180), str(self.board[j].count(0)), (0, 0, 0), font=self.font)

        self.bg = Image.new('RGBA', (2170, 2170), color=(44, 164, 100))

        for i in range(10, 1451, 360):
            for j in range(10, 1451, 360):
                # draw = ImageDraw.Draw(self.square)
                # draw.text((100, 90), '1', (0, 0, 0), font=self.font)
                self.bg.paste(self.square, (i, j))

        for i, j in zip(range(10, 1811, 360), range(5)):
            self.bg.paste(self.voltorb_row[j], (i, 1810))

        for i, j in zip(range(10, 1811, 360), range(5)):
            self.bg.paste(self.voltorb_col[j], (1810, i))

        self.voltorb_tile = Image.new('RGBA', (350, 350), color=(188, 140, 133))
        self.voltorb_tile.paste(vline, (0, 0))
        self.voltorb_tile.paste(vline, (340, 0))
        self.voltorb_tile.paste(hline, (0, 0))
        self.voltorb_tile.paste(hline, (0, 340))
        self.voltorb_tile.alpha_composite(voltorb_png, (95, 95))

        self.font = ImageFont.truetype('arial.ttf', 160)

        self.tile_1 = Image.new('RGBA', (350, 350), color=(188, 140, 133))
        self.tile_1.paste(vline, (0, 0))
        self.tile_1.paste(vline, (340, 0))
        self.tile_1.paste(hline, (0, 0))
        self.tile_1.paste(hline, (0, 340))
        draw = ImageDraw.Draw(self.tile_1)
        draw.text((130, 90), '1', (0, 0, 0), font=self.font)

        self.tile_2 = Image.new('RGBA', (350, 350), color=(188, 140, 133))
        self.tile_2.paste(vline, (0, 0))
        self.tile_2.paste(vline, (340, 0))
        self.tile_2.paste(hline, (0, 0))
        self.tile_2.paste(hline, (0, 340))
        draw = ImageDraw.Draw(self.tile_2)
        draw.text((130, 90), '2', (0, 0, 0), font=self.font)

        self.tile_3 = Image.new('RGBA', (350, 350), color=(188, 140, 133))
        self.tile_3.paste(vline, (0, 0))
        self.tile_3.paste(vline, (340, 0))
        self.tile_3.paste(hline, (0, 0))
        self.tile_3.paste(hline, (0, 340))
        draw = ImageDraw.Draw(self.tile_3)
        draw.text((130, 90), '3', (0, 0, 0), font=self.font)

    def create(self, name):
        self.bg.save('Voltorb Boards/' + name + '.png')

    def edit(self, name, temp):
        pos = [temp[0], int(temp[1])]
        if pos[0].lower() == 'a':
            pos[0] = 1
        elif pos[0].lower() == 'b':
            pos[0] = 2
        elif pos[0].lower() == 'c':
            pos[0] = 3
        elif pos[0].lower() == 'd':
            pos[0] = 4
        elif pos[0].lower() == 'e':
            pos[0] = 5
        if not self.flip[pos[0]-1][pos[1]-1]:
            if self.board[pos[0]-1][pos[1]-1] == 0:
                self.bg.paste(self.voltorb_tile, (pos[1]*360 - 350, pos[0]*360 - 350))
                self.bg.save('Voltorb Boards/' + name + '.png')
                return -1
            elif self.board[pos[0]-1][pos[1]-1] == 1:
                self.bg.paste(self.tile_1, (pos[1]*360 - 350, pos[0]*360 - 350))
            elif self.board[pos[0]-1][pos[1]-1] == 2:
                self.bg.paste(self.tile_2, (pos[1]*360 - 350, pos[0]*360 - 350))
            elif self.board[pos[0]-1][pos[1]-1] == 3:
                self.bg.paste(self.tile_3, (pos[1]*360 - 350, pos[0]*360 - 350))
            self.flip[pos[0]-1][pos[1]-1] = True
            self.bg.save('Voltorb Boards/' + name + '.png')

            flag = False
            for i in range(5):
                for j in range(5):
                    if self.board[i][j] > 1 and not self.flip[i][j]:
                        flag = True
            if not flag:
                return str(self.board[pos[0]-1][pos[1]-1]) + 'x'
            return self.board[pos[0]-1][pos[1]-1]
        return 0

    def edit_all(self, name, rowcol, num):
        if rowcol == 'row':
            if num.lower() == 'a':
                num = 1
            elif num.lower() == 'b':
                num = 2
            elif num.lower() == 'c':
                num = 3
            elif num.lower() == 'd':
                num = 4
            elif num.lower() == 'e':
                num = 5
            coins = 1
            for i in range(5):
                if not self.flip[num-1][i]:
                    if self.board[num-1][i] == 0:
                        self.bg.paste(self.voltorb_tile, ((i+1)*360 - 350, num*360 - 350))
                        coins = -1
                    elif self.board[num-1][i] == 1:
                        self.bg.paste(self.tile_1, ((i+1)*360 - 350, num*360 - 350))
                    elif self.board[num-1][i] == 2:
                        self.bg.paste(self.tile_2, ((i+1)*360 - 350, num*360 - 350))
                        if coins != -1:
                            coins *= 2
                    elif self.board[num-1][i] == 3:
                        self.bg.paste(self.tile_3, ((i+1)*360 - 350, num*360 - 350))
                        if coins != -1:
                            coins *= 3
                    self.flip[num-1][i] = True

            self.bg.save('Voltorb Boards/' + name + '.png')
            flag = False
            for i in range(5):
                for j in range(5):
                    if self.board[i][j] > 1 and not self.flip[i][j]:
                        flag = True
            if not flag:
                return str(coins) + 'x'
            return coins
        num = int(num)
        coins = 1
        for i in range(5):
            if self.board[i][num-1] == 0:
                self.bg.paste(self.voltorb_tile, (num*360 - 350, (i+1)*360 - 350))
                coins = -1
            elif self.board[i][num-1] == 1:
                self.bg.paste(self.tile_1, (num*360 - 350, (i+1)*360 - 350))
            elif self.board[i][num-1] == 2:
                self.bg.paste(self.tile_2, (num*360 - 350, (i+1)*360 - 350))
                if coins != -1:
                    coins *= 2
            elif self.board[i][num-1] == 3:
                self.bg.paste(self.tile_3, (num*360 - 350, (i+1)*360 - 350))
                if coins != -1:
                    coins *= 3
            self.flip[i][num-1] = True

        self.bg.save('Voltorb Boards/' + name + '.png')
        flag = False
        for i in range(5):
            for j in range(5):
                if self.board[i][j] > 1 and not self.flip[i][j]:
                    flag = True
        if not flag:
            return str(coins) + 'x'
        return coins

    def quit(self, name):
        os.remove('Voltorb Boards/' + str(name) + '.png')
