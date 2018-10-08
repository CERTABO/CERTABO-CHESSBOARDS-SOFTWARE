from __future__ import print_function
import cPickle as pickle
import os  # , Queue
import time
import threading

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


class EngineThread(threading.Thread):
    def __init__(self, move_history, difficulty, *args, **kwargs):
        self.move_history = move_history
        self.please_stop = False
        self.stop_engine = False
        self.engine_running = False
        self.engine = None
        self.best_move = None
        self.difficulty = difficulty
        self.stop_sent = False
        super(EngineThread, self).__init__(*args, **kwargs)

    def run(self):
        logging.info('Starting engine...')
        self.engine = Engine(depth=self.difficulty)
        logging.info('Setting position to %s', self.move_history)
        self.engine.setposition(self.move_history)
        self.engine.go()
        while True:
            best_move = self.engine.trybestmove()
            if best_move:
                self.best_move = best_move['move']
                break
            if self.stop_engine and not self.stop_sent:
                self.engine.put('stop')
                self.stop_sent = True
        self.engine.kill()

    def stop(self):
        self.stop_engine = True


def main():
    logging.basicConfig(level='DEBUG')
    et = EngineThread(difficulty=25, move_history=[])
    et.start()
    time.sleep(3)
    et.stop()
    et.join()
    print(et.best_move)


if __name__ == '__main__':
    main()