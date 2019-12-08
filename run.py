from __future__ import print_function
import sys
import argparse

DEBUG = False
DEBUG_FAST = False

TO_EXE = getattr(sys, "frozen", False)

XRESOLUTION = 1920

import time as tt
from datetime import datetime, timedelta
from select import *
from socket import *

import chess.pgn
import chess
import os
import platform
import pygame
import stockfish
import pypolyglot
import subprocess
import logging
import logging.handlers
import Queue
from collections import deque
import random

from constants import CERTABO_SAVE_PATH, CERTABO_DATA_PATH, MAX_DEPTH_DEFAULT

from messchess import RomEngineThread

for d in (CERTABO_SAVE_PATH, CERTABO_DATA_PATH):
    try:
        os.makedirs(d)
    except OSError:
        pass


if not DEBUG_FAST:
    logging.basicConfig(level="DEBUG", format="%(asctime)s:%(module)s:%(message)s")
    logger = logging.getLogger()
    filehandler = logging.handlers.TimedRotatingFileHandler(
        os.path.join(CERTABO_DATA_PATH, "certabo.log"), backupCount=12
    )
    logger.addHandler(filehandler)


import codes
from utils import port2number, port2udp, find_port, get_engine_list, get_book_list, coords_in
from publish import Publisher


stockfish.TO_EXE = TO_EXE

parser = argparse.ArgumentParser()
parser.add_argument("--port")
parser.add_argument("--publish", help="URL to publish data")
parser.add_argument("--game-id", help="Game ID")
parser.add_argument("--game-key", help="Game key")
parser.add_argument("--robust", help="Robust", action="store_true")
parser.add_argument("--syzygy", help="Syzygy path", default=os.path.join(CERTABO_DATA_PATH, 'syzygy'))
parser.add_argument("--hide-cursor", help="Hide cursor", action="store_true")
parser.add_argument("--max-depth", help="Maximum depth", type=int, default=MAX_DEPTH_DEFAULT)
args = parser.parse_args()

if args.port is None:
    portname = find_port()
else:
    portname = args.port
port = port2number(portname)

board_listen_port, gui_listen_port = port2udp(port)
logging.info('GUI: Board listen port: %s, gui listen port: %s', board_listen_port, gui_listen_port)

SEND_SOCKET = ("127.0.0.1", board_listen_port)  # send to
LISTEN_SOCKET = ("127.0.0.1", gui_listen_port)  # listen to

pgn_queue = None
publisher = None

DEFAULT_ENGINES = ("stockfish", "houdini", "komodo", "fire", "lczero")


class GameClock:
    def __init__(self):
        self.time_constraint = 'unlimited'
        self.time_total_minutes = 5
        self.time_increment_seconds = 8
        self.time_white_left = None
        self.time_black_left = None
        self.waiting_for_player = -99
        self.game_overtime = False
        self.game_overtime_winner = -99
        self.initial_moves = 0
        self.human_color = None
        self.move_duration = 0
        self.moves_duration = deque(maxlen=10)
        self.clock = pygame.time.Clock()

    def start(self):
        if self.time_constraint == 'blitz':
            self.time_total_minutes = 5
            self.time_increment_seconds = 0
        elif self.time_constraint == 'rapid':
            self.time_total_minutes = 10
            self.time_increment_seconds = 0
        elif self.time_constraint == 'classical':
            self.time_total_minutes = 15
            self.time_increment_seconds = 15

        self.time_white_left = float(self.time_total_minutes * 60)
        self.time_black_left = float(self.time_total_minutes * 60)
        self.waiting_for_player = -99
        self.game_overtime = False
        self.game_overtime_winner = -99
        self.initial_moves = len(chessboard.move_stack)
        self.human_color = play_white
        self.move_duration = 0
        self.moves_duration.clear()
        self.clock.tick()

    def update(self):

        if self.time_constraint == 'unlimited':
            return False

        if self.game_overtime:
            return True

        # Let time only start after both players do x moves
        moves = len(chessboard.move_stack)
        if moves - self.initial_moves > -1:  # Set > 1 to start only after 2 moves

            turn = chessboard.turn
            # If player changed
            if not self.waiting_for_player == turn:
                # Increment timer
                if self.waiting_for_player == 1:
                    self.time_white_left += self.time_increment_seconds
                elif self.waiting_for_player == 0:
                    self.time_black_left += self.time_increment_seconds

                # Store move duration for human player
                if not turn == self.human_color:
                    if self.move_duration > .01:
                        self.moves_duration.append(self.move_duration)
                    # print(self.moves_duration)
                self.move_duration = 0

                # Resume clock for other player
                self.waiting_for_player = turn
                self.clock.tick()

            else:
                self.clock.tick()
                change = float(self.clock.get_time()) / 1000
                self.move_duration += change
                if turn == 1:
                    self.time_white_left -= change
                    if self.time_white_left <= 0:
                        self.game_overtime = True
                        self.game_overtime_winner = 0
                        self.time_white_left = 0
                else:
                    self.time_black_left -= change
                    if self.time_black_left <= 0:
                        self.game_overtime = True
                        self.game_overtime_winner = 1
                        self.time_black_left = 0

            return self.game_overtime

    def display(self):
        if self.time_constraint == 'unlimited':
            return

        cols = [110]
        rows = [5, 40]

        black_minutes = int(self.time_black_left // 60)
        black_seconds = int(self.time_black_left % 60)
        color = grey
        if self.time_black_left <= 10:
            color = red
        button('{:02d}:{:02d}'.format(black_minutes, black_seconds), cols[0], rows[0], color=color, text_color=white, padding=(1, 1, 1, 1))

        white_minutes = int(self.time_white_left // 60)
        white_seconds = int(self.time_white_left % 60)
        color = lightestgrey
        if self.time_white_left <= 10:
            color = red
        button('{:02d}:{:02d}'.format(white_minutes, white_seconds), cols[0], rows[1], color=color, text_color=black, padding=(1, 1, 1, 1))

    def sample_ai_move_duration(self):

        if time_constraint == 'unlimited':
            return 0

        n = len(self.moves_duration)
        mean = 3
        std = 1.5

        if n > 0:
            mean = sum(self.moves_duration) / float(n)

        if n > 1:
            ss = sum((x - mean)**2 for x in self.moves_duration)
            std = (ss/(n-1))**0.5

        # print(self.moves_duration)
        # print(mean, std)
        return random.gauss(mean, std)


def make_publisher():
    global pgn_queue, publisher
    if publisher:
        publisher.stop()
    pgn_queue = Queue.Queue()
    publisher = Publisher(args.publish, pgn_queue, args.game_id, args.game_key)
    publisher.start()
    return pgn_queue, publisher


def publish():
    global pgn_queue
    pgn_queue.put(generate_pgn())


def do_poweroff(proc):
    if args.publish:
        publisher.stop()
    if platform.system() == "Windows":
        subprocess.call(["taskkill", "/F", "/T", "/PID", str(proc.pid)])
    else:
        subprocess.call(["kill", str(proc.pid)])
    pygame.display.quit()
    pygame.quit()
    sys.exit()


f = open("screen.ini", "rb")
try:
    XRESOLUTION = int(f.readline().split(" #")[0])
    logging.info("%s", XRESOLUTION)
    if XRESOLUTION == 1380:
        XRESOLUTION = 1366
except:
    logging.info("Cannot read resolution from screen.ini")
if XRESOLUTION != 480 and XRESOLUTION != 1366 and XRESOLUTION != 1920:
    logging.info("Wrong value xscreensize.ini = %s, setting 1366", XRESOLUTION)
    XRESOLUTION = 1366
try:
    s = f.readline().split(" #")[0]
    if s == "fullscreen":
        fullscreen = True
    else:
        fullscreen = False
except:
    fullscreen = False
    logging.info("Cannot read 'fullscreen' or 'window' as second line from screen.ini")
f.close()

# define set of colors
green = 0, 200, 0
darkergreen = 0, 180, 0
red = 200, 0, 0
black = 0, 0, 0
blue = 0, 0, 200
white = 255, 255, 255
terminal_text_color = 0xCF, 0xE0, 0x9A
grey = 100, 100, 100
lightgrey = 190, 190, 190
lightestgrey = 230, 230, 230

if TO_EXE:
    if platform.system() == "Windows":
        usb_command = ["usbtool.exe"]
    else:
        usb_command = ["./usbtool"]
else:
    usb_command = ["python", "usbtool.py"]
if portname is not None:
    usb_command.extend(["--port", portname])
logging.debug("Calling %s", usb_command)
usb_proc = subprocess.Popen(usb_command)

if not DEBUG_FAST:
    tt.sleep(1)  # time to make stable COMx connection

icon = pygame.image.load('certabo.png')
pygame.display.set_icon(icon)

os.environ["SDL_VIDEO_WINDOW_POS"] = "90,50"
pygame.mixer.init()
pygame.init()

# auto reduce a screen's resolution
infoObject = pygame.display.Info()
xmax, ymax = infoObject.current_w, infoObject.current_h
logging.info("Xmax = %s", xmax)
logging.info("XRESOLUTION = %s", XRESOLUTION)
if xmax < XRESOLUTION:
    XRESOLUTION = 1366
if xmax < XRESOLUTION:
    XRESOLUTION = 480

if XRESOLUTION == 480:
    screen_width, screen_height = 480, 320
elif XRESOLUTION == 1920:
    screen_width, screen_height = 1500, 1000
elif XRESOLUTION == 1366:
    screen_width, screen_height = 900, 600
x_multiplier, y_multiplier = float(screen_width) / 480, float(screen_height) / 320

if fullscreen:
    scr = pygame.display.set_mode(
        (screen_width, screen_height),
        pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.FULLSCREEN,
        32,
    )
else:
    scr = pygame.display.set_mode(
        (screen_width, screen_height), pygame.HWSURFACE | pygame.DOUBLEBUF, 32
    )

pygame.display.set_caption("Chess software")
font = pygame.font.Font("Fonts//OpenSans-Regular.ttf", int(13 * y_multiplier))
font_large = pygame.font.Font("Fonts//OpenSans-Regular.ttf", int(19 * y_multiplier))

scr.fill(black)  # clear screen
pygame.display.flip()  # copy to screen

# change mouse cursor to be unvisible - not needed for Windows!
if args.hide_cursor:
   mc_strings = '        ','        ','        ','        ','        ','        ','        ','        '
   cursor,mask = pygame.cursors.compile( mc_strings )
   cursor_sizer = ((8, 8), (0, 0), cursor, mask)
   pygame.mouse.set_cursor(*cursor_sizer)

# ----------- load sprites
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
    "stale-mate-banner",
    "five-fold-repetition-banner",
    "seventy-five-moves-banner",
    "insufficient-material-banner",
)

sprite = {}
for name in names:
    if XRESOLUTION == 480:
        path = "sprites//"
    elif XRESOLUTION == 1920:
        path = "sprites_1920//"
    elif XRESOLUTION == 1366:
        path = "sprites_1380//"
    sprite[name] = pygame.image.load(path + name + ".png")


sound = {}
sound_names = (
    "move",
)

for _sound_name in sound_names:
    try:
        sound[_sound_name] = pygame.mixer.Sound('sounds/{}.wav'.format(_sound_name))
    except:
        logging.error('Unable to load `{}` sound'.format(_sound_name))


def play_sound(sound_name):
    global sound
    try:
        s = sound[sound_name]
    except KeyError:
        return
    s.play()


# show sprite by name from names
def show(name, x, y):
    img = sprite[name]
    scr.blit(img, (x * x_multiplier, y * y_multiplier))
    widget_width, widget_height = img.get_size()
    return (
        x,
        y,
        x + int(widget_width // x_multiplier),
        y + int(widget_height // y_multiplier)
    )


def txt(s, x, y, color):
    img = font.render(s, 22, color)  # string, blend, color, background color
    pos = x * x_multiplier, y * y_multiplier
    scr.blit(img, pos)
    text_width, text_height = img.get_size()
    return (
        x + int(text_width // x_multiplier),
        y + int(text_height // y_multiplier)
    )


def txt_large(s, x, y, color):
    img = font_large.render(s, 22, color)  # string, blend, color, background color
    pos = x * x_multiplier, y * y_multiplier
    scr.blit(img, pos)
    text_width, text_height = img.get_size()
    return (
        x + int(text_width // x_multiplier),
        y + int(text_height // y_multiplier)
    )


def button(text, x, y, padding=(5, 5, 5, 5), color=white, text_color=grey, font=font_large, font_size=22, align='center'):
    ptop, pleft, pbottom, pright = padding
    text_width, text_height = font.size(text)
    widget_width = pleft * x_multiplier + text_width + pright * x_multiplier
    widget_height = ptop * y_multiplier + text_height + pbottom * y_multiplier

    if align == 'right':
        x -= int(widget_width/2)

    pygame.draw.rect(
        scr, color, (x * x_multiplier, y * y_multiplier, widget_width, widget_height)
    )
    img = font.render(text, font_size, text_color)
    pos = (x + pleft) * x_multiplier, (y + ptop) * y_multiplier
    scr.blit(img, pos)
    return (
        x,
        y,
        x + int(widget_width // x_multiplier),
        y + int(widget_height // y_multiplier),
    )


# Show chessboard using FEN string like
# "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
FEN = {
    "b": "black_bishop",
    "k": "black_king",
    "n": "black_knight",
    "p": "black_pawn",
    "q": "black_queen",
    "r": "black_rook",
    "B": "white_bishop",
    "K": "white_king",
    "N": "white_knight",
    "P": "white_pawn",
    "Q": "white_queen",
    "R": "white_rook",
}


chessboard = chess.Board()
board_state = chessboard.fen()
move = []

def show_board(FEN_string, x0, y0):
    show("chessboard_xy", x0, y0)
    if rotate180:
        FEN_string = "/".join(
            row[::-1] for row in reversed(FEN_string.split(" ")[0].split("/"))
        )
    x, y = 0, 0
    for c in FEN_string:
        if c in FEN:
            show(FEN[c], x0 + 26 + 31.8 * x, y0 + 23 + y * 31.8)
            x += 1
        elif c == "/":  # new line
            x = 0
            y += 1
        elif c == " ":
            break
        else:
            x += int(c)


letter = "a", "b", "c", "d", "e", "f", "g", "h"


def show_board_and_animated_move(FEN_string, move, x0, y0):
    piece = ""
    if rotate180:
        FEN_string = "/".join(
            row[::-1] for row in reversed(FEN_string.split(" ")[0].split("/"))
        )

    xa = letter.index(move[0])
    ya = 8 - int(move[1])
    xb = letter.index(move[2])
    yb = 8 - int(move[3])

    if rotate180:
        xa = 7 - xa
        ya = 7 - ya
        xb = 7 - xb
        yb = 7 - yb

    xstart, ystart = x0 + 26 + 31.8 * xa, y0 + 23 + ya * 31.8
    xend, yend = x0 + 26 + 31.8 * xb, y0 + 23 + yb * 31.8

    show("chessboard_xy", x0, y0)
    x, y = 0, 0
    for c in FEN_string:

        if c in FEN:
            if x != xa or y != ya:
                show(FEN[c], x0 + 26 + 31.8 * x, y0 + 23 + y * 31.8)
            else:
                piece = FEN[c]
            x += 1
        elif c == "/":  # new line
            x = 0
            y += 1
        elif c == " ":
            break
        else:
            x += int(c)
            # pygame.display.flip() # copy to screen
    if piece == "":
        return
    logging.info("%s", piece)
    for i in range(20):
        x, y = 0, 0
        show("chessboard_xy", x0, y0)
        for c in FEN_string:
            if c in FEN:
                if x != xa or y != ya:
                    show(FEN[c], x0 + 26 + 31.8 * x, y0 + 23 + y * 31.8)
                x += 1
            elif c == "/":  # new line
                x = 0
                y += 1
            elif c == " ":
                break
            else:
                x += int(c)

        xp = xstart + (xend - xstart) * i / 20.0
        yp = ystart + (yend - ystart) * i / 20.0
        show(piece, xp, yp)
        # print x,y
        # tt.sleep(0.1)
        pygame.display.flip()  # copy to screen
        tt.sleep(0.01)


def generate_pgn():
    global play_white, human_game
    move_history = [_move.uci() for _move in chessboard.move_stack]
    game = chess.pgn.Game()
    game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
    if play_white:
        game.headers["White"] = "Human"
        game.headers["Black"] = "Computer" if not human_game else "Human"
    else:
        game.headers["White"] = "Computer" if not human_game else "Human"
        game.headers["Black"] = "Human"
    game.headers["Result"] = chessboard.result()
    game.setup(chess.Board(starting_position, chess960=chess960))
    node = game.add_variation(chess.Move.from_uci(move_history[0]))
    for move in move_history[1:]:
        node = node.add_variation(chess.Move.from_uci(move))
    exporter = chess.pgn.StringExporter()
    return game.accept(exporter)


# ------------- start point --------------------------------------------------------

timeout = datetime.now() + timedelta(milliseconds=500)

old_left_click = 0

T = datetime.now() + timedelta(milliseconds=100)
x, y = 0, 0

window = "home"  # name of current page
dialog = ""  # dialog inside the window
# window="resume"

timer = 0
play_white = True
side_to_move = "white"
syzygy_available = os.path.exists(args.syzygy)
enable_syzygy=syzygy_available
difficulty = 0
terminal_lines = ["Game started", "Terminal text here"]
chess960 = False


def terminal_print(s, newline=True):
    global terminal_lines
    if newline:
        terminal_lines = [terminal_lines[1], s]
    else:
        terminal_lines[1] = "{}{}".format(terminal_lines[1], s)


pressed_key = ""
hint_text = ""
starting_position = chess.STARTING_FEN
name_to_save = ""

rotate180 = False
board_letters = "a", "b", "c", "d", "e", "f", "g", "h"
previous_board_click = ""  # example: "e2"
board_click = ""  # example: "e2"
do_ai_move = True
do_user_move = False
conversion_dialog = False
human_game = False
use_board_position = False
renew = True
left_click = False
game_clock = GameClock()

engine = "stockfish"
rom = False
book = ""

saved_files = []
resume_file_selected = 0
resume_file_start = 0  # starting filename to show
resuming_new_game = False

sock = socket(AF_INET, SOCK_DGRAM)
sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
sock.bind(LISTEN_SOCKET)
sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
recv_list = [sock]
new_usb_data = False
usb_data_exist = False

codes.load_calibration(port)
calibration = False
calibration_samples_counter = 0
calibration_samples = []

usb_data_history_depth = 3
usb_data_history = range(usb_data_history_depth)
usb_data_history_filled = False
usb_data_history_i = 0
move_detect_tries = 0
move_detect_max_tries = 3

banner_right_places = False
banners_counter = 0
game_process_just_startted = True
waiting_for_user_move = False

new_setup = False
current_engine_page = 0


def send_leds(message='\x00' * 8): 
    
    # logging.info("Sending leds: {}".format([ord(c) for c in message]))
    sock.sendto(message, SEND_SOCKET)

send_leds('\xff' * 8)

scr.fill(white)  # clear screen
show("start-up-logo", 7, 0)
pygame.display.flip()  # copy to screen
if not DEBUG_FAST:
    tt.sleep(2)
send_leds()

poweroff_time = datetime.now()


while True:
    t = datetime.now()  # current time

    # event from system & keyboard
    for event in pygame.event.get():  # all values in event list
        if event.type == pygame.QUIT:
            do_poweroff(usb_proc)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                do_poweroff(usb_proc)
            if event.key == pygame.K_h:
                window = "home"
            if event.key == pygame.K_a:
                pass

    recv_ready, wtp, xtp = select(recv_list, [], [], 0.002)

    if recv_ready:
        try:
            data, addr = sock.recvfrom(2048)
            usb_data = map(int, data.split(" "))
            new_usb_data = True
            usb_data_exist = True

        except:
            logging.info("No new data from usb.exe, perhaps chess board not connected")

    scr.fill(white)  # clear screen

    x, y = pygame.mouse.get_pos()  # mouse position
    x = x / x_multiplier
    y = y / y_multiplier

    mbutton = pygame.mouse.get_pressed()
    if DEBUG:
        txt(str((x, y)), 80, 300, lightgrey)
    if mbutton[0] == 1 and old_left_click == 0:
        left_click = True
    else:
        left_click = False

    if x < 110 and y < 101 and mbutton[0] == 1:
        if datetime.now() - poweroff_time >= timedelta(seconds=2):
            do_poweroff(usb_proc)
    else:
        poweroff_time = datetime.now()

    show("logo", 8, 6)
    # -------------- home ----------------
    if window == "home":

        if new_usb_data:
            new_usb_data = False

            if usb_data_history_i >= usb_data_history_depth:
                usb_data_history_filled = True
                usb_data_history_i = 0

            if DEBUG:
                logging.info("usb_data_history_i = %s", usb_data_history_i)
            usb_data_history[usb_data_history_i] = usb_data[:]
            usb_data_history_i += 1
            if usb_data_history_filled:
                usb_data_processed = codes.statistic_processing(usb_data_history, False)
                if usb_data_processed != []:
                    test_state = codes.usb_data_to_FEN(usb_data_processed, rotate180)
                    if test_state != "":
                        board_state = test_state
                else:
                    logging.info("found unknown piece, filter processing")

            if calibration:
                calibration_samples.append(usb_data)
                logging.info("    adding new calibration sample")
                calibration_samples_counter += 1
                if calibration_samples_counter >= 15:
                    logging.info(
                        "------- we have collected enough samples for averaging ----"
                    )
                    usb_data = codes.statistic_processing_for_calibration(
                        calibration_samples, False
                    )
                    # print usb_data
                    codes.calibration(usb_data, new_setup, port)
                    board_state = codes.usb_data_to_FEN(usb_data, rotate180)
                    calibration = False

                    # "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            # do a calibration
        show("new_game", 5, 149)
        if not args.robust:
            show("resume_game", 5, 149 + 40)
        show("setup", 5, 149 + 80)
        show("new-setup", 5, 149 + 120)

        show_board(board_state, 178, 40)
        show("welcome", 111, 6)

        if calibration:
            show("please-wait", 253, 170)

        if left_click:

            if 6 < x < 102 and 232 < y < 265:
                logging.info("calibration")
                if usb_data_exist:
                    calibration = True
                    new_setup = False
                    calibration_samples_counter = 0
                    calibration_samples = []
                    calibration_samples.append(usb_data)
            if 6 < x < 102 and y >= 265:
                logging.info("New setup calibration")
                if usb_data_exist:
                    calibration = True
                    new_setup = True
                    calibration_samples_counter = 0
                    calibration_samples = []
                    calibration_samples.append(usb_data)

            if 6 < x < 123 and 150 < y < 190:  # new game pressed
                window = "new game"
                send_leds()

            if 6 < x < 163 and 191 < y < 222:  # resume pressed
                window = "resume"
                # update saved files list to load
                files = os.listdir(CERTABO_SAVE_PATH)
                saved_files = [v for v in files if ".pgn" in v]
                saved_files_time = []
                terminal_lines = ["", ""]

                for name in saved_files:
                    saved_files_time.append(
                        tt.gmtime(
                            os.stat(os.path.join(CERTABO_SAVE_PATH, name)).st_mtime
                        )
                    )

    # ---------------- Resume game dialog ----------------
    elif window == "resume":
        txt_large("Select game name to resume", 159, 1, black)
        show("resume_back", 107, 34)
        show("resume_game", 263, 283)
        show("back", 3, 146)
        show("delete-game", 103, 283)

        pygame.draw.rect(
            scr,
            lightestgrey,
            (
                113 * x_multiplier,
                41 * y_multiplier + resume_file_selected * 29 * y_multiplier,
                330 * x_multiplier,
                30 * y_multiplier,
            ),
        )  # selection

        for i in range(len(saved_files)):
            if i > 7:
                break
            txt_large(saved_files[i + resume_file_start][:-4], 117, 41 + i * 29, grey)
            v = saved_files_time[i]

            txt_large(
                "%d-%d-%d  %d:%d"
                % (v.tm_year, v.tm_mon, v.tm_mday, v.tm_hour, v.tm_min),
                300,
                41 + i * 29,
                lightgrey,
            )

        if dialog == "delete":
            show("hide_back", 0, 0)

            pygame.draw.rect(scr, lightgrey, (200 + 2, 77 + 2, 220, 78))
            pygame.draw.rect(scr, white, (200, 77, 220, 78))
            txt_large("Delete the game ?", 200 + 32, 67 + 15, grey)
            show("back", 200 + 4, 77 + 40)
            show("confirm", 200 + 4 + 112, 77 + 40)

            if left_click:
                if (77 + 40 - 5) < y < (77 + 40 + 30):
                    dialog = ""
                    if x > (200 + 105):  # confirm button
                        logging.info("do delete")
                        os.unlink(
                            os.path.join(
                                CERTABO_SAVE_PATH,
                                saved_files[resume_file_selected + resume_file_start],
                            )
                        )

                        # update saved files list to load

                        files = os.listdir(CERTABO_SAVE_PATH)
                        saved_files = [v for v in files if ".pgn" in v]
                        saved_files_time = []
                        for name in saved_files:
                            saved_files_time.append(
                                tt.gmtime(
                                    os.stat(
                                        os.path.join(CERTABO_SAVE_PATH, name)
                                    ).st_mtime
                                )
                            )

                        resume_file_selected = 0
                        resume_file_start = 0

        if left_click:

            if 7 < x < 99 and 150 < y < 179:  # back button
                window = "home"

            if 106 < x < 260 and 287 < y < 317:  # delete button
                dialog = "delete"  # start delete confirm dialog on the page

            if 107 < x < 442 and 40 < y < 274:  # pressed on file list
                i = (int(y) - 41) / 29
                if i < len(saved_files):
                    resume_file_selected = i

            if 266 < x < 422 and 286 < y < 316:  # Resume button
                logging.info("Resuming game")
                with open(
                    os.path.join(
                        CERTABO_SAVE_PATH,
                        saved_files[resume_file_selected + resume_file_start],
                    ),
                    "rb",
                ) as f:
                    _game = chess.pgn.read_game(f)
                if _game:
                    chessboard = _game.end().board()
                    _node = _game
                    while _node.variations:
                        _node = _node.variations[0]
                    play_white = _game.headers["White"] == "Human"
                    starting_position = _game.board().fen()

                    logging.info("Move history - %s", [_move.uci() for _move in _game.main_line()])
                    previous_board_click = ""
                    board_click = ""
                    do_ai_move = False
                    do_user_move = False
                    conversion_dialog = False
                    waiting_for_user_move = False
                    banner_place_pieces = True
                    resuming_new_game = True

                    window = "new game"
            if 448 < x < 472:  # arrows
                if 37 < y < 60:  # arrow up
                    if resume_file_start > 0:
                        resume_file_start -= 1
                elif 253 < y < 284:
                    if (resume_file_start + 8) < len(saved_files):
                        resume_file_start += 1

    # ---------------- Save game dialog ----------------
    elif window == "save":

        txt_large("Enter game name to save", 159, 41, grey)
        show("terminal", 139, 80)
        txt_large(
            name_to_save, 273 - len(name_to_save) * (51 / 10.0), 86, terminal_text_color
        )

        # show keyboard
        keyboard_buttons = (
            ("1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-"),
            ("q", "w", "e", "r", "t", "y", "u", "i", "o", "p"),
            ("a", "s", "d", "f", "g", "h", "j", "k", "l"),
            ("z", "x", "c", "v", "b", "n", "m"),
        )

        lenx = 42  # size of buttons
        leny = 38  # size of buttons

        ky = 128
        x0 = 11

        hover_key = ""

        pygame.draw.rect(
            scr,
            lightgrey,
            (
                431 * x_multiplier,
                81 * y_multiplier,
                lenx * x_multiplier - 2,
                leny * y_multiplier - 2,
            ),
        )  # back space
        txt_large("<", (431 + 14), (81 + 4), black)

        for row in keyboard_buttons:
            kx = x0
            for key in row:
                pygame.draw.rect(
                    scr,
                    lightgrey,
                    (
                        kx * x_multiplier,
                        ky * y_multiplier,
                        lenx * x_multiplier - 2,
                        leny * y_multiplier - 2,
                    ),
                )
                txt_large(key, kx + 14, ky + 4, black)
                if kx < x < (kx + lenx) and ky < y < (ky + leny):
                    hover_key = key
                kx += lenx
            ky += leny
            x0 += 20

        pygame.draw.rect(
            scr,
            lightgrey,
            (
                x0 * x_multiplier + lenx * x_multiplier,
                ky * y_multiplier,
                188 * x_multiplier,
                leny * y_multiplier - 2,
            ),
        )  # spacebar
        if (x0 + lenx) < x < (x0 + lenx + 188) and ky < y < (ky + leny):
            hover_key = " "
        show("save", 388, 264)
        if 388 < x < (388 + 100) and 263 < y < (263 + 30):
            hover_key = "save"
        if 431 < x < (431 + lenx) and 81 < y < (81 + leny):
            hover_key = "<"

            # ----- process buttons -----
        if left_click:

            if hover_key != "":
                if hover_key == "save":
                    OUTPUT_PGN = os.path.join(
                        CERTABO_SAVE_PATH, "{}.pgn".format(name_to_save)
                    )
                    with open(OUTPUT_PGN, "w") as f:
                        f.write(generate_pgn())
                    window = "game"
                    # banner_do_move = False
                    previous_board_click = ""
                    board_click = ""
                    left_click = False
                    conversion_dialog = False

                elif hover_key == "<":
                    if len(name_to_save) > 0:
                        name_to_save = name_to_save[: len(name_to_save) - 1]
                else:
                    if len(name_to_save) < 22:
                        name_to_save += hover_key

    # ---------------- game dialog ----------------
    elif window == "game":

        if new_usb_data:
            new_usb_data = False
            if DEBUG:
                logging.info("Virtual board: %s", chessboard.fen())

            banners_counter += 1

            if usb_data_history_i >= usb_data_history_depth:
                usb_data_history_filled = True
                usb_data_history_i = 0

                # print "usb_data_history_i = ",usb_data_history_i
            usb_data_history[usb_data_history_i] = usb_data[:]
            usb_data_history_i += 1
            if usb_data_history_filled:
                usb_data_processed = codes.statistic_processing(usb_data_history, False)
                if usb_data_processed != []:
                    test_state = codes.usb_data_to_FEN(usb_data_processed, rotate180)
                    if test_state != "":
                        board_state_usb = test_state
                        game_process_just_started = False

                        # compare virtual board state and state from usb
                        s1 = chessboard.board_fen()
                        s2 = board_state_usb.split(" ")[0]
                        if s1 != s2:
                            if waiting_for_user_move:
                                try:
                                    move_detect_tries += 1
                                    move = codes.get_moves(chessboard, board_state_usb)
                                except codes.InvalidMove:
                                    if move_detect_tries > move_detect_max_tries:
                                        terminal_print("Invalid move")
                                else:
                                    move_detect_tries = 0
                                    if move:
                                        waiting_for_user_move = False
                                        do_user_move = True
                            else:
                                if DEBUG:
                                    logging.info("Place pieces on their places")
                                banner_right_places = True
                                if not human_game:
                                    if play_white != chessboard.turn:
                                        banner_place_pieces = True
                                else:
                                    banner_place_pieces = True
                        else:
                            if DEBUG:
                                logging.info("All pieces on right places")
                            send_leds()
                            banner_right_places = False
                            banner_place_pieces = False
                            # start with black, do move just right after right initial board placement

                            if not human_game:
                                if chessboard.turn != play_white:
                                    do_ai_move = True
                                else:
                                    do_ai_move = False

                            if (
                                not game_process_just_started
                                and not do_user_move
                                and not do_ai_move
                            ):
                                banner_place_pieces = False
                                waiting_for_user_move = True
                else:
                    logging.info("found unknown piece, filter processing")

        game_overtime = game_clock.update()
        game_clock.display()
        show("terminal", 179, 3)

        txt(terminal_lines[0], 183, 3, terminal_text_color)
        txt(terminal_lines[1], 183, 18, terminal_text_color)
        txt_large(hint_text, 96, 185 + 22, grey)

        # buttons
        if not rom:
            show("take_back", 5, 140 + 22)
        if not human_game and not rom:
            show("hint", 5, 140 + 40 + 22)
        show("save", 5, 140 + 100)
        show("exit", 5, 140 + 140)

        if dialog == "exit":
            show_board(chessboard.fen(), 178, 40)
            pygame.draw.rect(
                scr,
                lightgrey,
                (
                    229 * x_multiplier,
                    79 * y_multiplier,
                    200 * x_multiplier,
                    78 * y_multiplier,
                ),
            )
            pygame.draw.rect(
                scr,
                white,
                (
                    227 * x_multiplier,
                    77 * y_multiplier,
                    200 * x_multiplier,
                    78 * y_multiplier,
                ),
            )
            txt("Save the game or not ?", 227 + 37, 77 + 15, grey)
            show("save", 238, 77 + 40)
            show("exit", 238 + 112, 77 + 40)

            if left_click:
                if (77 + 40 - 5) < y < (77 + 40 + 30):
                    if x > (238 + 105):  # exit button
                        chessboard = chess.Board()
                        dialog = ""
                        window = "home"
                        terminal_lines = ["", ""]
                        pressed_key = ""
                        hint_text = ""
                        previous_board_click = ""  # example: "e2"
                        board_click = ""  # example: "e2"
                        if rom:
                            rom_engine.kill()
                    else:  # save button
                        dialog = ""
                        window = "save"
                        previous_board_click = ""
                        board_click = ""

        else:  # usual game process

            # AI MOVE
            if not human_game and do_ai_move and not chessboard.is_game_over() and not game_overtime:
                do_ai_move = False
                got_polyglot_result = False
                if not book:
                    got_polyglot_result = False
                else:
                    finder = pypolyglot.Finder(book, chessboard, difficulty + 1)
                    best_move = finder.bestmove()
                    got_polyglot_result = (best_move is not None)

                if got_polyglot_result:
                    ai_move = best_move.lower()
                else:
                    move_list = [_move.uci() for _move in chessboard.move_stack]
                    if not rom:
                        proc = stockfish.EngineThread(
                            move_list,
                            difficulty + 1,
                            engine=engine,
                            starting_position=starting_position,
                            chess960=chess960,
                            syzygy_path=args.syzygy if enable_syzygy else None,
                        )
                        proc.start()
                    else:
                        rom_engine.go(move_list)

                    got_fast_result = False
                    waiting_ai_move = True
                    ai_move_duration = game_clock.sample_ai_move_duration()
                    ai_move_start_time = tt.time()
                    while waiting_ai_move or ai_move_start_time + ai_move_duration > tt.time():
                        if not rom:
                            waiting_ai_move = proc.is_alive()
                        else:
                            waiting_ai_move = rom_engine.waiting_ai_move()

                        # Event from system & keyboard
                        for event in pygame.event.get():  # all values in event list
                            if event.type == pygame.QUIT:
                                if args.publish:
                                    publisher.stop()
                                pygame.display.quit()
                                pygame.quit()
                                # if rom:
                                #     rom_engine.kill()
                                sys.exit()

                        # Display board
                        show_board(chessboard.fen(), 178, 40)
                        pygame.draw.rect(
                            scr,
                            lightgrey,
                            (
                                229 * x_multiplier,
                                79 * y_multiplier,
                                200 * x_multiplier,
                                78 * y_multiplier,
                            ),
                        )
                        pygame.draw.rect(
                            scr,
                            white,
                            (
                                227 * x_multiplier,
                                77 * y_multiplier,
                                200 * x_multiplier,
                                78 * y_multiplier,
                            ),
                        )
                        game_overtime = game_clock.update()
                        game_clock.display()

                        txt_large("Analysing...", 227 + 55, 77 + 8, grey)
                        if not rom:
                            show("force-move", 247, 77 + 39)
                        pygame.display.flip()  # copy to screen

                        x, y = pygame.mouse.get_pos()  # mouse position
                        x = x / x_multiplier
                        y = y / y_multiplier

                        mbutton = pygame.mouse.get_pressed()

                        if (not rom and (mbutton[0] == 1 and 249 < x < 404 and 120 < y < 149)) or game_overtime:  # pressed Force move button
                            logging.info("------------------------------------")
                            if not rom:
                                proc.stop()
                                proc.join()
                                ai_move = proc.best_move
                                got_fast_result = True
                            break

                        # tt.sleep(0.5)

                    if not got_fast_result:
                        if not rom:
                            ai_move = proc.best_move.lower()
                        else:
                            ai_move = rom_engine.best_move

                if not game_overtime:
                    play_sound('move')
                    logging.info("AI move: %s", ai_move)

                    # highlight right LED
                    i, value, i_source, value_source = codes.move2led(
                        ai_move, rotate180
                    )  # error here if checkmate before
                    message = ""
                    for j in range(8):
                        if j != i and j != i_source:
                            message += chr(0)
                        elif j == i and j == i_source:
                            message += chr(value + value_source)
                        elif j == i:
                            message += chr(value)
                        else:
                            message += chr(value_source)

                    send_leds(message)

                    # banner_do_move = True
                    if not args.robust:
                        show_board_and_animated_move(chessboard.fen(), ai_move, 178, 40)

                    try:
                        chessboard.push_uci(ai_move)
                        logging.info("   AI move: %s", ai_move)
                        logging.info("after AI move: %s", chessboard.fen())
                        side = ("white", "black")[int(chessboard.turn)]
                        terminal_print("{} move: {}".format(side, ai_move))
                        if args.publish:
                            publish()
                    except:
                        logging.info("   ----invalid chess_engine move! ---- %s", ai_move)
                        logging.exception("Exception: ")
                        terminal_print(ai_move + " - invalid move !")

                    logging.info("\n\n%s", chessboard.fen())

                    if chessboard.is_check():
                        terminal_print(" check!", False)

                    if chessboard.is_checkmate():
                        logging.info("mate!")

                    if chessboard.is_stalemate():
                        logging.info("stalemate!")

            # user move
            if do_user_move and not chessboard.is_game_over() and not game_overtime:
                do_user_move = False
                try:
                    for m in move:
                        chessboard.push_uci(m)
                        logging.info("   user move: %s", m)
                        side = ("white", "black")[int(chessboard.turn)]
                        terminal_print("{} move: {}".format(side, m))
                        if not human_game:
                            do_ai_move = True
                            hint_text = ""
                        if args.publish:
                            publish()
                except:
                    logging.info("   ----invalid user move! ---- %s", move)
                    logging.exception("Exception: ")
                    terminal_print("%s - invalid move !" % move)
                    previous_board_click = ""
                    board_click = ""
                    waiting_for_user_move = True

                if chessboard.is_check():
                    terminal_print(" check!", False)

                if chessboard.is_checkmate():
                    logging.info("mate! we won!")

                if chessboard.is_stalemate():
                    logging.info("stalemate!")

            show_board(chessboard.fen(), 178, 40)

            # -------------------- show banners -------------------------
            #            if banners_counter%2 ==0:
            x0, y0 = 5, 127
            if banner_right_places:
                if not chessboard.move_stack or banner_place_pieces:
                    show("place-pieces", x0 + 2, y0 + 2)
                else:
                    show("move-certabo", x0, y0 + 2)
            #                pygame.draw.rect(scr, black, (x0+2, y0+2, 167, 28) )
            #                txt("Please place pieces",x0+5+22,y0+4,white)
            if waiting_for_user_move:
                show("do-your-move", x0 + 2, y0 + 2)
                # pygame.draw.rect(scr, black, (x0+2, y0+2, 167, 28) )
                # txt("Please move your piece",x0+14,y0+4,white)

            if game_overtime:
                if game_clock.game_overtime_winner == 1:
                    button('White wins', 270, 97, color=grey, text_color=white)
                else:
                    button('Black wins', 270, 97, color=grey, text_color=white)
            elif chessboard.is_game_over():
                if chessboard.is_checkmate():
                    gameover_banner = "check-mate-banner"
                elif chessboard.is_stalemate():
                    gameover_banner = "stale-mate-banner"
                elif chessboard.is_fivefold_repetition():
                    gameover_banner = "five-fold-repetition-banner"
                elif chessboard.is_seventyfive_moves():
                    gameover_banner = "seventy-five-moves-banner"
                elif chessboard.is_insufficient_material():
                    gameover_banner = "insufficient-material-banner"
                show(gameover_banner, 227, 97)

            if conversion_dialog:
                pygame.draw.rect(scr, lightgrey, (227 + 2, 77 + 2, 200, 78))
                pygame.draw.rect(scr, white, (227, 77, 200, 78))
                txt("Select conversion to:", 227 + 37, 77 + 7, grey)
                if play_white:  # show four icons
                    icons = "white_bishop", "white_knight", "white_queen", "white_rook"
                    icon_codes = "B", "N", "Q", "R"
                else:
                    icons = "black_bishop", "black_knight", "black_queen", "black_rook"
                    icon_codes = "b", "n", "q", "r"
                i = 0
                for icon in icons:
                    show(icon, 227 + 15 + i, 77 + 33)
                    i += 50

            if left_click:
                if conversion_dialog:
                    if (227 + 15) < x < (424) and (77 + 33) < y < (77 + 33 + 30):
                        i = (x - (227 + 15 - 15)) / 50
                        if i < 0:
                            i = 0
                        if i > 3:
                            i = 3
                        icon = icon_codes[i]
                        if len(move[0]) == 4:
                            move[0] += icon
                            logging.info("move for conversion: %s", move[0])
                            conversion_dialog = False
                            do_user_move = True
                else:

                    if 6 < x < 123 and (140 + 140) < y < (
                        140 + 140 + 40
                    ):  # Exit button
                        dialog = "exit"  # start dialog inside Game page

                    if 6 < x < 127 and (143 + 22) < y < (174 + 22):  # Take back button
                        if (human_game and len(chessboard.move_stack) >= 1) or (
                            not human_game and not rom and len(chessboard.move_stack) >= 2
                        ):
                            logging.info("--------- before take back: ")
                            logging.info("Board state: %s", chessboard.fen())
                            logging.info(
                                "%s", [_move.uci() for _move in chessboard.move_stack]
                            )
                            if human_game:
                                chessboard.pop()
                            else:
                                chessboard.pop()
                                chessboard.pop()

                            logging.info("--------- after take back: ")
                            logging.info(
                                "%s", [_move.uci() for _move in chessboard.move_stack]
                            )
                            logging.info("Board state: {}".format(chessboard.fen()))
                            logging.info("----------------------------------")

                            previous_board_click = ""
                            board_click = ""

                            waiting_for_user_move = False
                            do_user_move = False
                            banner_right_places = True
                            banner_place_pieces = True

                            hint_text = ""
                        else:
                            logging.info(
                                "cannot do takeback, move count = %s",
                                len(chessboard.move_stack),
                            )

                    if 6 < x < 89 and (183 + 22) < y < (216 + 22):  # Hint button
                        got_polyglot_result = False
                        if not book:
                            got_polyglot_result = False
                        else:
                            finder = pypolyglot.Finder(book, chessboard, difficulty + 1)
                            best_move = finder.bestmove()
                            got_polyglot_result = (best_move is not None)
                        
                        if got_polyglot_result:
                            hint_text = best_move
                        elif not rom:
                            proc = stockfish.EngineThread(
                                [_move.uci() for _move in chessboard.move_stack],
                                difficulty + 1,
                                engine=engine,
                                starting_position=starting_position,
                                chess960=chess960,
                                syzygy_path=args.syzygy if enable_syzygy else None,
                            )
                            proc.start()
                            # print "continues..."

                            show_board(chessboard.fen(), 178, 40)
                            pygame.draw.rect(
                                scr,
                                lightgrey,
                                (
                                    229 * x_multiplier,
                                    79 * y_multiplier,
                                    200 * x_multiplier,
                                    78 * y_multiplier,
                                ),
                            )
                            pygame.draw.rect(
                                scr,
                                white,
                                (
                                    227 * x_multiplier,
                                    77 * y_multiplier,
                                    200 * x_multiplier,
                                    78 * y_multiplier,
                                ),
                            )
                            txt_large("Analysing...", 227 + 55, 77 + 8, grey)
                            show("force-move", 247, 77 + 39)
                            pygame.display.flip()  # copy to screen

                            got_fast_result = False
                            while proc.is_alive():  # thinking
                                # event from system & keyboard
                                for event in pygame.event.get():  # all values in event list
                                    if event.type == pygame.QUIT:
                                        publisher.stop()
                                        pygame.display.quit()
                                        pygame.quit()
                                        sys.exit()

                                x, y = pygame.mouse.get_pos()  # mouse position
                                x = x / x_multiplier
                                y = y / y_multiplier

                                mbutton = pygame.mouse.get_pressed()
                                # txt_large("%d %d %s"%(x,y,str(mbutton)),0,0,black)
                                # pygame.display.flip() # copy to screen
                                if (
                                    mbutton[0] == 1 and 249 < x < 404 and 120 < y < 149
                                ):  # pressed Force move button
                                    proc.stop()
                                    proc.join()
                                    hint_text = proc.best_move
                                    got_fast_result = True
                                    mbutton = (0, 0, 0)
                                    break

                            if not got_fast_result:
                                hint_text = proc.best_move

                    if 6 < x < 78 and 244 < y < 272:  # Save button
                        window = "save"
                        previous_board_click = ""
                        board_click = ""

    # ---------------- new game dialog ----------------
    elif window == "new game":
        if dialog == "select time":

            time_total_minutes = game_clock.time_total_minutes
            time_increment_seconds = game_clock.time_increment_seconds

            cols = [150, 195]
            rows = [15, 70, 105, 160, 200]

            show("hide_back", 0, 0)
            button("Custom Time Settings", cols[0], rows[0], color=green, text_color=white)
            txt_large("Minutes per side:", cols[0], rows[1], black)
            minutes_button_area = button('{}'.format(time_total_minutes), cols[1], rows[2], color=grey, text_color=white)
            minutes_less_button_area = button("<", minutes_button_area[0] - 5, rows[2], text_color=grey, color=white, align='right', padding=(5, 2, 5, 2))
            minutes_less2_button_area = button("<<", minutes_less_button_area[0] - 5, rows[2], text_color=grey, color=white, align='right', padding=(5, 0, 5, 0))
            minutes_more_button_area = button(">", minutes_button_area[2] + 5, rows[2], text_color=grey, color=white, padding=(5, 2, 5, 2))
            minutes_more2_button_area = button(">>", minutes_more_button_area[2] + 5, rows[2], text_color=grey, color=white, padding=(5, 0, 5, 0))

            txt_large("Increment in seconds:", cols[0], rows[3], black)
            seconds_button_area = button('{}'.format(time_increment_seconds), cols[1], rows[4], color=grey, text_color=white)
            seconds_less_button_area = button("<", seconds_button_area[0] - 5, rows[4], text_color=grey, color=white, align='right', padding=(5, 2, 5, 2))
            seconds_less2_button_area = button("<<", seconds_less_button_area[0] - 5, rows[4], text_color=grey, color=white, align='right', padding=(5, 0, 5, 0))
            seconds_more_button_area = button(">", seconds_button_area[2] + 5, rows[4], text_color=grey, color=white, padding=(5, 2, 5, 2))
            seconds_more2_button_area = button(">>", seconds_more_button_area[2] + 5, rows[4], text_color=grey, color=white, padding=(5, 0, 5, 0))

            done_button_area = button("Done", 415, 275, color=darkergreen, text_color=white)

            if left_click:
                if coords_in(x, y, minutes_less_button_area):
                    time_total_minutes -= 1
                elif coords_in(x, y, minutes_less2_button_area):
                    time_total_minutes -= 10
                elif coords_in(x, y, minutes_more_button_area):
                    time_total_minutes += 1
                elif coords_in(x, y, minutes_more2_button_area):
                    time_total_minutes += 10
                elif coords_in(x, y, seconds_less_button_area):
                    time_increment_seconds -= 1
                elif coords_in(x, y, seconds_less2_button_area):
                    time_increment_seconds -= 10
                elif coords_in(x, y, seconds_more_button_area):
                    time_increment_seconds += 1
                elif coords_in(x, y, seconds_more2_button_area):
                    time_increment_seconds += 10

                game_clock.time_total_minutes = max(time_total_minutes, 1)
                game_clock.time_increment_seconds = max(time_increment_seconds, 0)

                if coords_in(x, y, done_button_area):
                    dialog = ""
        elif dialog == "select_engine":
            engines_per_page = 6
            show("hide_back", 0, 0)
            engines = get_engine_list()
            txt_large("Select engine:", 250, 20, black)
            # draw engine buttons
            button_coords = []
            engine_button_x = 250
            engine_button_y = 50
            engine_button_vertical_margin = 5
            engine_list = get_engine_list()
            if (current_engine_page + 1) * engines_per_page > len(engine_list):
                current_engine_page = len(engine_list) // engines_per_page
            page_engines = engine_list[
                current_engine_page
                * engines_per_page : (current_engine_page + 1)
                * engines_per_page
            ]
            has_next = len(engine_list) > (current_engine_page + 1) * engines_per_page
            has_prev = current_engine_page > 0
            for engine_name in page_engines:
                engine_button_area = button(
                    engine_name,
                    engine_button_x,
                    engine_button_y,
                    text_color=white,
                    color=darkergreen if engine == engine_name else grey,
                )
                button_coords.append(("select_engine", engine_name, engine_button_area))
                _, _, _, engine_button_y = engine_button_area
                engine_button_y += engine_button_vertical_margin
            done_button_area = button(
                "Done", 415, 275, color=darkergreen, text_color=white
            )
            button_coords.append(("select_engine_done", None, done_button_area))
            if has_next:
                next_page_button_area = button(
                    " > ", 415, 150, color=darkergreen, text_color=white
                )
                button_coords.append(("next_page", None, next_page_button_area))
            if has_prev:
                prev_page_button_area = button(
                    " < ", 200, 150, color=darkergreen, text_color=white
                )
                button_coords.append(("prev_page", None, prev_page_button_area))
            if left_click:
                for action, value, (lx, ty, rx, by) in button_coords:
                    if lx < x < rx and ty < y < by:
                        if action == "select_engine":
                            engine = value
                        elif action == "select_engine_done":
                            dialog = ""
                        elif action == "next_page":
                            current_engine_page += 1
                        elif action == "prev_page":
                            current_engine_page -= 1
                        break
        elif dialog == "select_book":
            show("hide_back", 0, 0)
            txt_large("Select book:", 250, 20, black)
            button_coords = []
            book_button_x = 250
            book_button_y = 50
            book_button_vertical_margin = 5
            book_list = get_book_list()
            for book_name in book_list:
                book_button_area = button(
                    book_name,
                    book_button_x,
                    book_button_y,
                    text_color=white,
                    color=darkergreen if book == book_name else grey,
                )
                button_coords.append(("select_book", book_name, book_button_area))
                _, _, _, book_button_y = book_button_area
                book_button_y += book_button_vertical_margin
            done_button_area = button(
                "Done", 415, 275, color=darkergreen, text_color=white
            )
            button_coords.append(("select_book_done", None, done_button_area))
            if left_click:
                for action, value, (lx, ty, rx, by) in button_coords:
                    if lx < x < rx and ty < y < by:
                        if action == "select_book":
                            book = value
                        elif action == "select_book_done":
                            dialog = ""
                        break
        else:
            cols = [20, 150, 190, 280, 460]
            rows = [15, 60, 105, 150, 195, 225, 255, 270]

            txt_x, _ = txt_large("Mode:", cols[1], rows[0]+5, grey)
            human_game_button_area = button(
                "Human",
                txt_x + 15,
                rows[0],
                text_color=white,
                color=darkergreen if human_game else grey,
            )
            _, _, human_game_button_x, _ = human_game_button_area
            computer_game_button_area = button(
                "Engine",
                human_game_button_x + 5,
                rows[0],
                text_color=white,
                color=darkergreen if not human_game else grey,
            )
            _, _, computer_game_button_x, _ = computer_game_button_area
            flip_board_button_area = button(
                "Flip board",
                computer_game_button_x + 5,
                rows[0],
                text_color=white,
                color=darkergreen if rotate180 else grey,
            )
            use_board_position_button_area = button(
                "Use board position",
                cols[1],
                rows[1],
                text_color=white,
                color=darkergreen if use_board_position else grey,
            )
            # txt_large("Time:", 150, use_board_position_button_area[3]+5, grey)

            txt_x, _ = txt_large("Time:", cols[1], rows[2] + 5, grey)

            time_constraint = game_clock.time_constraint
            time_unlimited_button_area = button(
                u"\u221E",
                txt_x + 5,
                rows[2],
                text_color=white,
                color=darkergreen if time_constraint == 'unlimited' else grey,
                padding=(5, 10, 5, 10)
            )
            h_gap = 4
            time_blitz_button_area = button(
                "5+0",
                time_unlimited_button_area[2]+h_gap,
                rows[2],
                text_color=white,
                color=darkergreen if time_constraint == 'blitz' else grey,
            )
            time_rapid_button_area = button(
                "10+0",
                time_blitz_button_area[2]+h_gap,
                rows[2],
                text_color=white,
                color=darkergreen if time_constraint == 'rapid' else grey,
            )
            time_classical_button_area = button(
                "15+15",
                time_rapid_button_area[2]+h_gap,
                rows[2],
                text_color=white,
                color=darkergreen if time_constraint == 'classical' else grey,
            )

            time_custom_button_area = button(
                "Other",
                time_classical_button_area[2]+h_gap,
                rows[2],
                text_color=white,
                color=darkergreen if time_constraint == 'custom' else grey,
            )

            chess960_button_area = button(
                "Chess960",
                cols[1],
                rows[3],
                text_color=white,
                color=darkergreen if chess960 else grey,
            )

            if syzygy_available:
                syzygy_button_area = button(
                    "Syzygy",
                    chess960_button_area[2] + 5,
                    rows[3],
                    text_color=white,
                    color=darkergreen if enable_syzygy else grey,
                )

            if use_board_position:
                _, _, use_board_position_button_x, _ = use_board_position_button_area
                side_to_move_button_area = button(
                    "White to move" if side_to_move == "white" else "Black to move",
                    use_board_position_button_x + 5,
                    rows[1],
                    text_color=white if side_to_move == "black" else black,
                    color=black if side_to_move == "black" else lightestgrey,
                )
            else:
                side_to_move_button_area = None
            if human_game:
                depth_less_button_area = None
                depth_more_button_area = None
            else:
                txt_large("Engine: {}".format(engine), cols[1], rows[4]+5, grey)
                select_engine_button_area = button(
                    '...',
                    cols[-1],
                    rows[4],
                    text_color=white,
                    color=darkergreen,
                    padding=(0,5,0,5),
                    align='right'
                )

                book_repr = book
                if len(book_repr) > 20:
                    book_repr = "{}...".format(book_repr[:20])
                _, txt_y = txt_large("Book: {}".format(book_repr), cols[1], rows[5]+5, grey)
                select_book_button_area = button(
                    '...',
                    cols[-1],
                    rows[5],
                    text_color=white,
                    color=darkergreen,
                    padding=(0,5,0,5),
                    align='right'
                )

                txt_x, txt_y = txt("Depth:", cols[0], rows[4]+8, green)
                difficulty_button_area = button('{:02d}'.format(difficulty + 1), cols[0]+20, rows[5], color=grey, text_color=white)
                depth_less_button_area = button("<", difficulty_button_area[0]-5, rows[5], text_color=grey, color=white, align='right')
                depth_more_button_area = button(">", difficulty_button_area[2]+5, rows[5], text_color=grey, color=white)

                x0 = txt_x + 5
                y0 = rows[4] + 8
                if not human_game:
                    if difficulty == 0:
                        txt("Easiest", x0, y0, grey)
                    elif difficulty < 4:
                        txt("Easy", x0, y0, grey)
                    elif difficulty > 18:
                        txt("Hardest", x0, y0, grey)
                    elif difficulty > 10:
                        txt("Hard", x0, y0, grey)
                    else:
                        txt("Normal", x0, y0, grey)

            if not human_game:
                txt_x, _ = txt_large("Play as:", cols[1], rows[6]+5, green)
                sprite_color = "black"
                if play_white:
                    sprite_color = "white"
                color_button_area = show(sprite_color, txt_x + 5, rows[6])

            back_button_area = show("back", cols[0], rows[-1])
            start_button_area = show("start", cols[-1]-100, rows[-1])

            if left_click:
                if coords_in(x, y, human_game_button_area):
                    human_game = True
                if coords_in(x, y, computer_game_button_area):
                    human_game = False
                if coords_in(x, y, flip_board_button_area):
                    rotate180 = not rotate180
                if coords_in(x, y, use_board_position_button_area):
                    use_board_position = not use_board_position
                for time_button, time_string in zip((time_unlimited_button_area, time_blitz_button_area, time_rapid_button_area, time_classical_button_area),
                                                    ('unlimited', 'blitz', 'rapid', 'classical')):
                    if coords_in(x, y, time_button):
                        game_clock.time_constraint = time_string
                if coords_in(x, y, time_custom_button_area):
                    dialog = "select time"
                    game_clock.time_constraint = 'custom'
                if coords_in(x, y, chess960_button_area):
                    chess960 = not chess960
                if syzygy_available and coords_in(x, y, syzygy_button_area):
                    enable_syzygy = not enable_syzygy
                if coords_in(x, y, depth_less_button_area):
                    if difficulty > 0:
                        difficulty -= 1
                    else:
                        difficulty = args.max_depth - 1
                if coords_in(x, y, depth_more_button_area):
                    if difficulty < args.max_depth - 1:
                        difficulty += 1
                    else:
                        difficulty = 0
                if use_board_position:
                    if coords_in(x, y, side_to_move_button_area):
                        side_to_move = "white" if side_to_move == "black" else "black"
                if coords_in(x, y, select_engine_button_area):
                    dialog = "select_engine"
                    current_engine_page = 0
                if coords_in(x, y, select_book_button_area):
                    dialog = "select_book"

                if coords_in(x, y, color_button_area):
                    play_white = not play_white

                if coords_in(x, y, back_button_area):
                        window = "home"

                if coords_in(x, y, start_button_area):
                    window = "game"
                    if resuming_new_game:
                        resuming_new_game = False
                    else:
                        if not use_board_position:
                            chessboard = chess.Board()
                            starting_position = chessboard.fen()
                        else:
                            chessboard = chess.Board(chess960=chess960)
                            chessboard.clear()
                            chessboard.set_board_fen(board_state.split()[0])
                            chessboard.turn = side_to_move == 'white'
                            chessboard.set_castling_fen('KQkq')
                            starting_position = chessboard.fen()
                    terminal_print("New game, depth={}".format(difficulty + 1))
                    previous_board_click = ""
                    board_click = ""
                    do_user_move = False
                    do_ai_move = False
                    rom = engine.startswith('rom')
                    if rom:
                        rom_engine = RomEngineThread(depth=difficulty + 1, rom=engine.replace('rom-', ''))

                    conversion_dialog = False
                    waiting_for_user_move = False
                    game_process_just_started = True
                    banner_place_pieces = True

                    game_clock.start()

                    if args.publish:
                        make_publisher()

    left_click = False
    old_left_click = mbutton[0]

    #    pygame.draw.line(scr, red, (0,0), (100,100), 3)
    pygame.display.flip()  # copy to screen
    tt.sleep(0.005)
    T = datetime.now() - t
