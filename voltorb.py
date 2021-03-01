import random
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

        self.font = ImageFont.truetype('arial.ttf', 120)
        self.bg = Image.open('sprites/board.png')
        self.voltorb_tile = Image.open('sprites/voltorb_tile.png')
        self.tile_1 = Image.open('sprites/number_tile_1.png')
        self.tile_2 = Image.open('sprites/number_tile_2.png')
        self.tile_3 = Image.open('sprites/number_tile_3.png')
        self.hl_voltorb_tile = Image.open('sprites/hl_voltorb_tile.png')

        for i, j in zip(range(10, 1811, 360), range(5)):
            draw = ImageDraw.Draw(self.bg)
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
            draw.text((i+x, 1830), str(sum_num), (0, 0, 0), font=self.font)
            draw.text((i+240, 1990), str(vol_num), (0, 0, 0), font=self.font)

            if sum(self.board[j]) > 9:
                x = 180
            else:
                x = 240
            draw.text((1810+x, i+20), str(sum(self.board[j])), (0, 0, 0), font=self.font)
            draw.text((2050, i+180), str(self.board[j].count(0)), (0, 0, 0), font=self.font)

    def flip_all(self):
        for i in range(5):
            for j in range(5):
                if not self.flip[i][j]:
                    if self.board[i][j] == 0:
                        self.bg.paste(self.voltorb_tile, ((j+1)*360 - 350, (i+1)*360 - 350))
                    elif self.board[i][j] == 1:
                        self.bg.paste(self.tile_1, ((j+1)*360 - 350, (i+1)*360 - 350))
                    elif self.board[i][j] == 2:
                        self.bg.paste(self.tile_2, ((j+1)*360 - 350, (i+1)*360 - 350))
                    elif self.board[i][j] == 3:
                        self.bg.paste(self.tile_3, ((j+1)*360 - 350, (i+1)*360 - 350))
                    self.flip[i][j] = True

    def create(self, name):
        return self.bg

    def edit(self, name, temp):
        pos = [temp[0], int(temp[1])]
        pos[0] = ord(pos[0].upper()) - 64
        if not self.flip[pos[0]-1][pos[1]-1]:
            if self.board[pos[0]-1][pos[1]-1] == 0:
                self.bg.paste(self.hl_voltorb_tile, (pos[1]*360 - 350, pos[0]*360 - 350))
                self.flip[pos[0]-1][pos[1]-1] = True
                self.flip_all()
                return [-1, self.bg]
            elif self.board[pos[0]-1][pos[1]-1] == 1:
                self.bg.paste(self.tile_1, (pos[1]*360 - 350, pos[0]*360 - 350))
            elif self.board[pos[0]-1][pos[1]-1] == 2:
                self.bg.paste(self.tile_2, (pos[1]*360 - 350, pos[0]*360 - 350))
            elif self.board[pos[0]-1][pos[1]-1] == 3:
                self.bg.paste(self.tile_3, (pos[1]*360 - 350, pos[0]*360 - 350))
            self.flip[pos[0]-1][pos[1]-1] = True

            flag = False
            for i in range(5):
                for j in range(5):
                    if self.board[i][j] > 1 and not self.flip[i][j]:
                        flag = True
            if not flag:
                return [str(self.board[pos[0]-1][pos[1]-1]) + 'x', self.bg]
            return [self.board[pos[0]-1][pos[1]-1], self.bg]
        return [0, self.bg]

    def edit_all(self, name, rowcol, num):
        coins = 1
        if rowcol == 'row':
            num = ord(num.upper()) - 64
            for i in range(5):
                if not self.flip[num-1][i]:
                    if self.board[num-1][i] == 0:
                        self.bg.paste(self.hl_voltorb_tile, ((i+1)*360 - 350, num*360 - 350))
                        self.flip[num-1][i] = True
                        self.flip_all()
                        return [-1, self.bg]
                    elif self.board[num-1][i] == 1:
                        self.bg.paste(self.tile_1, ((i+1)*360 - 350, num*360 - 350))
                    elif self.board[num-1][i] == 2:
                        self.bg.paste(self.tile_2, ((i+1)*360 - 350, num*360 - 350))
                        coins *= 2
                    elif self.board[num-1][i] == 3:
                        self.bg.paste(self.tile_3, ((i+1)*360 - 350, num*360 - 350))
                        coins *= 3
                    self.flip[num-1][i] = True

            flag = False
            for i in range(5):
                for j in range(5):
                    if self.board[i][j] > 1 and not self.flip[i][j]:
                        flag = True
            if not flag:
                return [str(coins) + 'x', self.bg]
            return [coins, self.bg]
        num = int(num)
        for i in range(5):
            if self.board[i][num-1] == 0:
                self.bg.paste(self.hl_voltorb_tile, (num*360 - 350, (i+1)*360 - 350))
                self.flip[i][num-1] = True
                self.flip_all()
                return [-1, self.bg]
            elif self.board[i][num-1] == 1:
                self.bg.paste(self.tile_1, (num*360 - 350, (i+1)*360 - 350))
            elif self.board[i][num-1] == 2:
                self.bg.paste(self.tile_2, (num*360 - 350, (i+1)*360 - 350))
                coins *= 2
            elif self.board[i][num-1] == 3:
                self.bg.paste(self.tile_3, (num*360 - 350, (i+1)*360 - 350))
                coins *= 3
            self.flip[i][num-1] = True

        flag = False
        for i in range(5):
            for j in range(5):
                if self.board[i][j] > 1 and not self.flip[i][j]:
                    flag = True
        if not flag:
            return [str(coins) + 'x', self.bg]
        return [coins, self.bg]
