import os
import chess
import chess.polyglot
import logging
import time as tt
from constants import BOOK_PATH


TO_EXE = True

class Finder:
    def __init__(
        self,
        book,
        board,
        difficulty
    ):
        self.book_path = os.path.join(BOOK_PATH, book)
        self.board = board
        self.difficulty = difficulty
        self.reader = chess.polyglot.open_reader(self.book_path)
        
    def bestmove(self):
        tt.sleep(0.5)
        logging.info("Polyglot finding...")
        entry = self.reader.get(self.board)
        if entry is not None:
            logging.info("Polyglot found")
            best_move = entry.move.uci()
        else:
            logging.info("Polyglot not found")
            best_move = None
        return best_move

def main():
    logging.basicConfig(level="DEBUG")
    board = chess.Board('rnbqkbnr/pppp1ppp/8/4p2Q/4P3/8/PPPP1PPP/RNB1KBNR b KQkq - 1 2')
    et = Finder("performance.bin", board, 5)
    print(et.bestmove())

if __name__ == "__main__":
    main()
