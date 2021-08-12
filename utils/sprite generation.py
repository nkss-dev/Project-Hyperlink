import random
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

sq1 = Image.new('RGBA', (100, 100), color=(20, 132, 92))
sq2 = Image.new('RGBA', (100, 100), color=(44, 164, 100))

vline = Image.new('RGBA', (10, 350), color=(0, 0, 0))
hline = Image.new('RGBA', (350, 10), color=(0, 0, 0))

hl_vline = Image.new('RGBA', (10, 350), color=(255, 0, 0))
hl_hline = Image.new('RGBA', (350, 10), color=(255, 0, 0))

font = ImageFont.truetype('arial.ttf', 120)

square = Image.new('RGBA', (350, 350), color=(20, 132, 92))
square.paste(vline, (0, 0))
square.paste(vline, (340, 0))
square.paste(hline, (0, 0))
square.paste(hline, (0, 340))
square.paste(sq2, (125, 25))
square.paste(sq2, (25, 125))
square.paste(sq2, (225, 125))
square.paste(sq2, (125, 225))

voltorb = [Image.new('RGBA', (350, 350), color=(222, 112, 85)),
        Image.new('RGBA', (350, 350), color=(69, 167, 70)),
        Image.new('RGBA', (350, 350), color=(230, 159, 67)),
        Image.new('RGBA', (350, 350), color=(55, 146, 245)),
        Image.new('RGBA', (350, 350), color=(191, 101, 221))]

voltorb_png = Image.open('voltorb 160.png')

for i, j in zip(range(10, 1811, 360), range(5)):
    voltorb[j].paste(vline, (0, 0))
    voltorb[j].paste(vline, (340, 0))
    voltorb[j].paste(hline, (0, 0))
    voltorb[j].paste(hline, (0, 340))
    voltorb[j].paste(hline, (0, 150))
    voltorb[j].alpha_composite(voltorb_png, (20, 170))

bg = Image.new('RGBA', (2170, 2170), color=(44, 164, 100))

draw = ImageDraw.Draw(bg)
for i in range(10, 1451, 360):
    for j in range(10, 1451, 360):
        bg.paste(square, (i, j))
        draw.text((i+100, j+110), str(chr(int(j/350+65))) + str(int(i/350+1)), (0, 0, 0), font=font)

for i, j in zip(range(10, 1811, 360), range(5)):
    bg.paste(voltorb[j], (i, 1810))
    bg.paste(voltorb[j], (1810, i))

voltorb_tile = Image.new('RGBA', (350, 350), color=(188, 140, 133))
voltorb_tile.paste(vline, (0, 0))
voltorb_tile.paste(vline, (340, 0))
voltorb_tile.paste(hline, (0, 0))
voltorb_tile.paste(hline, (0, 340))
voltorb_tile.alpha_composite(voltorb_png, (95, 95))

hl_voltorb_tile = Image.new('RGBA', (350, 350), color=(188, 140, 133))
hl_voltorb_tile.paste(hl_vline, (0, 0))
hl_voltorb_tile.paste(hl_vline, (340, 0))
hl_voltorb_tile.paste(hl_hline, (0, 0))
hl_voltorb_tile.paste(hl_hline, (0, 340))
hl_voltorb_tile.alpha_composite(voltorb_png, (95, 95))

font = ImageFont.truetype('arial.ttf', 160)

tile_1 = Image.new('RGBA', (350, 350), color=(188, 140, 133))
tile_1.paste(vline, (0, 0))
tile_1.paste(vline, (340, 0))
tile_1.paste(hline, (0, 0))
tile_1.paste(hline, (0, 340))
draw = ImageDraw.Draw(tile_1)
draw.text((130, 90), '1', (0, 0, 0), font=font)

tile_2 = Image.new('RGBA', (350, 350), color=(188, 140, 133))
tile_2.paste(vline, (0, 0))
tile_2.paste(vline, (340, 0))
tile_2.paste(hline, (0, 0))
tile_2.paste(hline, (0, 340))
draw = ImageDraw.Draw(tile_2)
draw.text((130, 90), '2', (0, 0, 0), font=font)

tile_3 = Image.new('RGBA', (350, 350), color=(188, 140, 133))
tile_3.paste(vline, (0, 0))
tile_3.paste(vline, (340, 0))
tile_3.paste(hline, (0, 0))
tile_3.paste(hline, (0, 340))
draw = ImageDraw.Draw(tile_3)
draw.text((130, 90), '3', (0, 0, 0), font=font)

square.save('sprites/normal_tile.png')
voltorb_tile.save('sprites/voltorb_tile.png')
hl_voltorb_tile.save('sprites/hl_voltorb_tile.png')
tile_1.save('sprites/number_tile_1.png')
tile_2.save('sprites/number_tile_2.png')
tile_3.save('sprites/number_tile_3.png')
bg.save('sprites/board.png')
for i in range(5):
    voltorb[i].save('sprites/indicator_tile_' + str(i+1) + '.png')
