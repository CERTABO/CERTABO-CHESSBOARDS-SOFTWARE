from __future__ import print_function
import cPickle as pickle
import os  # , Queue
import logging
import threading
import chess
import chess.polyglot
from constants import DATA_PATH

TO_EXE = True

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
        self.engine_path = os.path.join(DATA_PATH, self.engine)
        self.board = board
        self.best_move = None
        self.difficulty = difficulty
        self.chess960 = chess960
        super(EngineThread, self).__init__(*args, **kwargs)

    def run(self):
        logging.info("Starting engine...")
        reader = chess.polyglot.open_reader(self.engine_path)
        entry = reader.get(self.board)
        if entry is not None:
            self.best_move = entry.move().uci()
        else:
            self.best_move = None
        return

def main():
    logging.basicConfig(level="DEBUG")
    board = chess.Board('rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2')
    et = EngineThread(board, difficulty=5, engine="performance.bin")
    et.start()
    et.join()
    print(et.best_move)


if __name__ == "__main__":
    main()
