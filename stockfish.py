from __future__ import print_function
import cPickle as pickle
import os  # , Queue
import time

from pystockfish import *

TO_EXE = True

# import multiprocessing

# Contempt Integer, Default: 0, Min: -100, Max: 100
# Roughly equivalent to "optimism." Positive values of contempt favor more "risky" play, 
# while negative values will favor draws. Zero is neutral.

# ?? Min Split Depth Integer, Default: 0, Min: 0, Max: 12

# Threads Integer, Default: 1, Min: 1, Max: 128
# The number of threads to use during the search. This number should be set to the number of cores in your CPU.

# Hash Integer, Default: 16, Min: 1, Max: 1048576
# The amount of memory to use for the hash during search,
# specified in MB (megabytes). This number should be smaller than the amount of physical memory for your system.

# Ponder Boolean, Default: True
# Whether or not the engine should analyze when it is the opponent's turn.

# MultiPV Integer, Default: 1, Min: 1, Max: 500
# The number of alternate lines of analysis to display. Specify 1 to just get the best line.
# Asking for more lines slows down the search.

# ?? Move Overhead Integer, Default: 30, Min: 0, Max:5000

# Minimum Thinking Time Integer, Default: 20, Min: 0, Max: 5000
# The minimum amount of time to analyze, in milliseconds.

# ?? Slow Mover Integer, Default: 70, Min: 10, Max: 1000

params = {
    "Contempt Factor": 0,
    "Min Split Depth": 0,
    "Threads": 2,
    "Hash": 128,
    "MultiPV": 1,
    "Skill Level": 20,
    "Move Overhead": 30,
    "Minimum Thinking Time": 20,
    "Slow Mover": 80
}
game = ""
small_game = ""


def ini(difficulty):
    global small_game
    #    game = Engine(depth=difficulty, param=params)
    #    small_game = Engine(depth=0, param=params)
    small_game = Engine(depth=0)
    # game = Engine(depth=0)
    return game


#    game_engine.setposition( move_history )
#    ai_move = game_engine.bestmove()['move'

proc = None
q = 0
best_move = ""


def get_move(q, move_history, difficulty):
    global game, best_move
    #    game = Engine(depth=difficulty, param=params)
    game = Engine(depth=difficulty)
    game.setposition(move_history)
    best_move = game.bestmove()
    # q.put( game.bestmove() )


def start_thinking_about_bestmove(move_history, difficulty):
    global proc
    f = open("move_history_tmp.p", "wb")
    pickle.dump((move_history, difficulty), f)
    f.flush()
    os.fsync(f)

    f.close()
    time.sleep(0.1)

    if TO_EXE:
        command = "move.exe"
    else:
        command = "python move.py"
    proc = subprocess.Popen(command, shell=True)
    print("proc.pid = ", proc.pid)
    return proc


def get_result_of_thinking():
    # time.sleep(0.1)
    f = open("bestmove.p", "rb")
    best_move = pickle.load(f)
    f.close()
    return best_move['move']


# get move value if Force move pressed
def get_fast_result(move_history):
    global proc

    # kill long process
    subprocess.call(['taskkill', '/F', '/T', '/PID', str(proc.pid)])
    # time.sleep(0.1)

    small_game.setposition(move_history)
    return small_game.bestmove()['move']
