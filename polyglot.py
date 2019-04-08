from __future__ import print_function
import cPickle as pickle
import os  # , Queue
import logging
import threading
import chess
import chess.polyglot
from constants import ENGINE_PATH

class EngineThread(threading.Thread):
    def __init__(
        self,
        board,
        difficulty,
        engine="polyglot",
        chess960=False,
        *args,
        **kwargs
    ):
        self.engine = engine
        self.engine_path = os.path.join(ENGINE_PATH, self.engine)
        self.board = board
        self.best_move = None
        self.difficulty = difficulty
        self.chess960 = chess960
        super(EngineThread, self).__init__(*args, **kwargs)

    def run(self):
        logging.info("Starting engine...")
        reader = chess.polyglot.open_reader(self.engine_path)
        entry = reader.find(self.board)
        self.best_move = entry.move().uci()
        return

def main():
    logging.basicConfig(level="DEBUG")
    board = chess.Board()
    et = EngineThread(board, difficulty=5, engine="performance.bin")
    et.start()
    et.join()
    print(et.best_move)


if __name__ == "__main__":
    main()
