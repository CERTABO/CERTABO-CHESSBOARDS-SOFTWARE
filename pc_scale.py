from __future__ import print_function
import PIL  # pip install pillow
from PIL import Image
import os


def resize(filename):
    img = Image.open("sprites//" + filename)  # pics for 480x320
    kx1 = 1500.0 / 480
    ky1 = 1000.0 / 320
    kx2 = 900.0 / 480
    ky2 = 600.0 / 320

    w1 = int(float(img.size[0]) * kx1)
    h1 = int(float(img.size[1]) * ky1)
    w2 = int(float(img.size[0]) * kx2)
    h2 = int(float(img.size[1]) * ky2)

    print(filename, img.size[0], w1, w2)
    img.close()

    img = Image.open("big_pngs//" + filename)  # pics for 480x320
    img1 = img.resize((w1, h1), PIL.Image.ANTIALIAS)
    img1.save("sprites_1920//" + filename)
    img1 = img.resize((w2, h2), PIL.Image.ANTIALIAS)
    img1.save("sprites_1380//" + filename)


names = (
    "black_bishop",
    "black_king",
    "black_knight",
    "black_pawn",
    "black_queen",
    "black_rook",
    "white_bishop",
    "white_king",
    "white_knight",
    "white_pawn",
    "white_queen",
    "white_rook",
    "terminal",
    "logo",
    "chessboard_xy",
    "new_game",
    "resume_game",
    "save",
    "exit",
    "hint",
    "setup",
    "take_back",
    "resume_back",
    "analysing",
    "back",
    "black",
    "confirm",
    "delete-game",
    "depth1",
    "depth2",
    "depth3",
    "depth4",
    "depth5",
    "depth6",
    "depth7",
    "depth8",
    "depth9",
    "depth10",
    "depth11",
    "depth12",
    "depth13",
    "depth14",
    "depth15",
    "depth16",
    "depth17",
    "depth18",
    "depth19",
    "depth20",
    "done",
    "force-move",
    "select-depth",
    "start",
    "welcome",
    "white",
    "hide_back",
    "start-up-logo",
    "do-your-move",
    "move-certabo",
    "place-pieces",
    "place-pieces-on-chessboard",
    "new-setup",
    "please-wait",
    "check-mate-banner",
)

sprite = {}
print(len(names))
for name in names:
    filename = name + ".png"
    img = Image.open("big_pngs//" + filename)

    # sprite[ name ] = pygame.image.load('sprites//'+name+'.png')
    # print name, img.size[0],img.size[1]
    resize(filename)

# no terminal.png, resume_back.png, black.png


# images = {
# "black_bishop":31, "black_king":31, "black_knight":31,"black_pawn":31,"black_queen":31,"black_rook":31,
# "white_bishop":31, "white_king":31, "white_knight":31,"white_pawn":31,"white_queen":31,"white_rook":#31,"terminal":38,
# "logo":120, "chessboard_xy":280, "new_game":38, "resume_game":38, "save":38,  "exit":38, "hint":38, "setup":38, "take_back":38,\

# "analysing":38, "back":38, "black":38, "confirm":38, "delete-game":38, "depth1":38, "depth2":38, "depth3":38, #"depth4":38,\
# "depth5":38, "depth6":38, "depth7":38, "depth8":38, "depth9":38, "depth10":38, "depth11":38, "depth12":38, #"depth13":38,\
# "depth14":38, "depth15":38, "depth16":38, "depth17":38, "depth18":38, "depth19":38, "depth20":38, "done":38,\
# "force-move":38,  "select-depth":38, "select-time":38, "start":38, "welcome":32, "white":38, "start-up-logo":319


# }

# sprite = {}
# for name in images:
#    print name, " resizing to height ",images[ name ]
#    resize( name+".png", images[ name ] )
