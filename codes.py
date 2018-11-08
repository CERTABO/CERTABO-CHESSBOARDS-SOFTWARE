from __future__ import print_function
import pickle
import os
import chess
import chess
from constants import CERTABO_DATA_PATH
import logging

# data conversion
p, r, n, b, k, q, P, R, N, B, K, Q = [], [], [], [], [], [], [], [], [], [], [], []

# for calibration
def cell_codes(n_cell, usb_data):  # n_cell from 0 to 63, 0 at left top
    result = []
    for i in range(5):
        result.append(usb_data[n_cell * 5 + i])
    return result


def compare_cells(x, y):
    # l = len( frozenset(x).intersection(y) )
    if x[0] == y[0] and x[1] == y[1] and x[2] == y[2] and x[3] == y[3] and x[4] == y[4]:
        return True
    else:
        return False


def get_calibration_file_name(port):
    if port is None:
        return "calibration.bin"
    else:
        return "calibration-com{}.bin".format(port + 1)


def load_calibration(port):
    global p, r, n, b, k, q, P, R, N, B, K, Q
    print("codes.py - loading calibration")
    try:
        p, r, n, b, k, q, P, R, N, B, K, Q = pickle.load(
            open(os.path.join(CERTABO_DATA_PATH, get_calibration_file_name(port)), "rb")
        )
    except (IOError, OSError):
        return False
    return True


def statistic_processing_for_calibration(samples, show_print):
    global letters
    result = []
    for n_cell in range(64):
        cells = []
        #        if show_print: print "\n    cell n =",n_cell,letter[n_cell%8]+str(8-n_cell/8), "   samples:"
        if show_print:
            print("\n    ", letter[n_cell % 8] + str(8 - n_cell / 8), "   samples:")
        for usb_data in samples:
            cells.append(cell_codes(n_cell, usb_data))
            if show_print:
                print(cell_codes(n_cell, usb_data))
        histograms = []
        for cell in cells:
            histogram = 0
            for c in cells:
                if compare_cells(cell, c):
                    histogram += 1
            histograms.append(histogram)

        max_value = max(histograms)
        max_index = histograms.index(max_value)

        # append cells[max_index] to result
        if show_print:
            print("---final code:", end=" ")
        for i in cells[max_index]:
            if show_print:
                print(i, end=" ")
            result.append(i)
        if show_print:
            print()

    return result


def get_name(cell):
    global p, r, n, b, k, q, P, R, N, B, K, Q
    c = ""
    if cell_empty(cell):
        c = "-"
    for cell_p in p:
        if compare_cells(cell, cell_p):
            c = "p"
    for cell_p in P:
        if compare_cells(cell, cell_p):
            c = "P"
    for cell_p in r:
        if compare_cells(cell, cell_p):
            c = "r"
    for cell_p in R:
        if compare_cells(cell, cell_p):
            c = "R"
    for cell_p in n:
        if compare_cells(cell, cell_p):
            c = "n"
    for cell_p in N:
        if compare_cells(cell, cell_p):
            c = "N"
    for cell_p in b:
        if compare_cells(cell, cell_p):
            c = "b"
    for cell_p in B:
        if compare_cells(cell, cell_p):
            c = "B"
    for cell_p in q:
        if compare_cells(cell, cell_p):
            c = "q"
    for cell_p in Q:
        if compare_cells(cell, cell_p):
            c = "Q"
    for cell_p in k:
        if compare_cells(cell, cell_p):
            c = "k"
    for cell_p in K:
        if compare_cells(cell, cell_p):
            c = "K"
    return c


def statistic_processing(samples, show_print):
    global letters
    result = []
    found_unknown_cell = False
    for n_cell in range(64):
        cells = []
        #        if show_print: print "\n    cell n =",n_cell,letter[n_cell%8]+str(8-n_cell/8), "   samples:"
        if show_print:
            print("\n    ", letter[n_cell % 8] + str(8 - n_cell / 8), "   samples:")
        for usb_data in samples:
            cells.append(cell_codes(n_cell, usb_data))
            if show_print:
                print(cell_codes(n_cell, usb_data))
        histograms = []

        known_cells = []
        for cell in cells:  # stack of history of cell codes for one cell
            name = get_name(cell)
            if name == "-":
                cell = 0, 0, 0, 0, 0
            if name != "":
                known_cells.append(cell)

        if len(known_cells) == 0:
            print(
                "Found only unknown cell codes in cell ",
                letter[n_cell % 8] + str(8 - n_cell / 8),
                ":",
            )
            for cell in cells:  # stack of history of cell codes for one cell
                print(cell)

            found_unknown_cell = True
            break

        for cell in known_cells:  # stack of history of cell codes for one cell
            histogram = 0
            for c in cells:
                if compare_cells(cell, c):
                    histogram += 1
            histograms.append(histogram)

        max_value = max(histograms)
        max_index = histograms.index(max_value)

        # append cells[max_index] to result
        if show_print:
            print("---final code:", end=" ")
        for i in known_cells[max_index]:
            if show_print:
                print(i, end=" ")
            result.append(i)
        if show_print:
            print()

    if found_unknown_cell:
        return []

    return result


# ---------------------------
def cell_empty(x):
    nzeros = 0
    for n in x:
        if n == 0:
            nzeros += 1
    if nzeros > 2:
        return True
    else:
        return False


def calibration(usb_data, new_setup, port):
    global p, r, n, b, k, q, P, R, N, B, K, Q
    prev_results = p, r, n, b, k, q, P, R, N, B, K, Q

    p, r, n, b, k, q, P, R, N, B, K, Q = [], [], [], [], [], [], [], [], [], [], [], []
    empty_cell = [0, 0, 0, 0, 0]
    # pawns
    for i in range(8):  # each place at board
        cell = cell_codes(8 + i, usb_data)
        if not compare_cells(cell, empty_cell):
            p.append(cell_codes(8 + i, usb_data))
        cell = cell_codes(48 + i, usb_data)
        if not cell_empty(cell):  # not empty
            P.append(cell_codes(48 + i, usb_data))

    r.append(cell_codes(0, usb_data))
    r.append(cell_codes(7, usb_data))
    R.append(cell_codes(56, usb_data))
    R.append(cell_codes(63, usb_data))

    n.append(cell_codes(1, usb_data))
    n.append(cell_codes(6, usb_data))
    N.append(cell_codes(57, usb_data))
    N.append(cell_codes(62, usb_data))

    b.append(cell_codes(2, usb_data))
    b.append(cell_codes(5, usb_data))
    B.append(cell_codes(58, usb_data))
    B.append(cell_codes(61, usb_data))

    q.append(cell_codes(3, usb_data))
    Q.append(cell_codes(59, usb_data))

    k.append(cell_codes(4, usb_data))
    K.append(cell_codes(60, usb_data))

    pp, rp, np, bp, kp, qp, Pp, Rp, Np, Bp, Kp, Qp = prev_results
    results = p, r, n, b, k, q, P, R, N, B, K, Q

    pn, rn, nn, bn, kn, qn, Pn, Rn, Nn, Bn, Kn, Qn = (
        p[:],
        r[:],
        n[:],
        b[:],
        k[:],
        q[:],
        P[:],
        R[:],
        N[:],
        B[:],
        K[:],
        Q[:],
    )

    def add_new(pnew, pcurrent, pprevious):
        for previous in pprevious:
            previous_not_in_current = True
            for current in pcurrent:
                if compare_cells(current, previous):
                    previous_not_in_current = False
                    break
            if previous_not_in_current:
                print("previous not in current")
                pnew.append(previous)
            else:
                print("previous in current")
        return pnew

    print("Q before =", Qn)

    pn = add_new(pn, p, pp)
    rn = add_new(rn, r, rp)
    nn = add_new(nn, n, np)
    bn = add_new(bn, b, bp)
    kn = add_new(kn, k, kp)
    qn = add_new(qn, q, qp)
    Pn = add_new(Pn, P, Pp)
    Rn = add_new(Rn, R, Rp)
    Nn = add_new(Nn, N, Np)
    Bn = add_new(Bn, B, Bp)
    Kn = add_new(Kn, K, Kp)
    Qn = add_new(Qn, Q, Qp)
    print("Q after =", Qn)

    # compare_cells( cell, cell_p )
    if not new_setup:
        print("------- not new setup ----")
        results = pn, rn, nn, bn, kn, qn, Pn, Rn, Nn, Bn, Kn, Qn
        p, r, n, b, k, q, P, R, N, B, K, Q = (
            pn,
            rn,
            nn,
            bn,
            kn,
            qn,
            Pn,
            Rn,
            Nn,
            Bn,
            Kn,
            Qn,
        )
    pickle.dump(results, open(os.path.join(CERTABO_DATA_PATH, get_calibration_file_name(port)), "wb"))

    print("----------------")
    # print r
    #    print compare_cells(p[0], p[1])

    for j in range(8):
        for i in range(8):
            cell = cell_codes(i + j * 8, usb_data)
            # print cell
            # print empty_cell
            if cell_empty(cell):
                print("-", end=" ")
            else:  # not empty
                for cell_p in p:
                    if compare_cells(cell, cell_p):
                        print("p", end=" ")
                for cell_p in P:
                    if compare_cells(cell, cell_p):
                        print("P", end=" ")
                for cell_p in r:
                    if compare_cells(cell, cell_p):
                        print("r", end=" ")
                for cell_p in R:
                    if compare_cells(cell, cell_p):
                        print("R", end=" ")
                for cell_p in n:
                    if compare_cells(cell, cell_p):
                        print("n", end=" ")
                for cell_p in N:
                    if compare_cells(cell, cell_p):
                        print("N", end=" ")
                for cell_p in b:
                    if compare_cells(cell, cell_p):
                        print("b", end=" ")
                for cell_p in B:
                    if compare_cells(cell, cell_p):
                        print("B", end=" ")
                for cell_p in q:
                    if compare_cells(cell, cell_p):
                        print("q", end=" ")
                for cell_p in Q:
                    if compare_cells(cell, cell_p):
                        print("Q", end=" ")
                for cell_p in k:
                    if compare_cells(cell, cell_p):
                        print("k", end=" ")
                for cell_p in K:
                    if compare_cells(cell, cell_p):
                        print("K", end=" ")
        print()


letter = "a", "b", "c", "d", "e", "f", "g", "h"


def move2led(move):
    i = letter.index(move[2])
    j = int(move[3])
    k = letter.index(move[0])
    l = int(move[1])
    return 8 - j, 2 ** i, 8 - l, 2 ** k


def usb_data_to_FEN(usb_data):
    global letter
    empty_cell = [0, 0, 0, 0, 0]
    s = ""
    was_unknown_piece = False
    for j in range(8):

        c = ""
        empty_cells_counter = 0
        for i in range(8):
            cell = cell_codes(i + j * 8, usb_data)
            c = "unknown"

            if cell_empty(cell):
                c = "-"
                empty_cells_counter += 1
            else:  # not empty

                for cell_p in p:
                    if compare_cells(cell, cell_p):
                        c = "p"
                for cell_p in P:
                    if compare_cells(cell, cell_p):
                        c = "P"
                for cell_p in r:
                    if compare_cells(cell, cell_p):
                        c = "r"
                for cell_p in R:
                    if compare_cells(cell, cell_p):
                        c = "R"
                for cell_p in n:
                    if compare_cells(cell, cell_p):
                        c = "n"
                for cell_p in N:
                    if compare_cells(cell, cell_p):
                        c = "N"
                for cell_p in b:
                    if compare_cells(cell, cell_p):
                        c = "b"
                for cell_p in B:
                    if compare_cells(cell, cell_p):
                        c = "B"
                for cell_p in q:
                    if compare_cells(cell, cell_p):
                        c = "q"
                for cell_p in Q:
                    if compare_cells(cell, cell_p):
                        c = "Q"
                for cell_p in k:
                    if compare_cells(cell, cell_p):
                        c = "k"
                for cell_p in K:
                    if compare_cells(cell, cell_p):
                        c = "K"

                if empty_cells_counter > 0 and c != "-":
                    s += str(empty_cells_counter)
                    empty_cells_counter = 0
                    s += c
                elif empty_cells_counter == 0 and c != "-":
                    s += c
                if c == "unknown":
                    #                    print "Unknown piece at cell n =",j*8+i, ", ",letter[i]+str(8-j)
                    print("Unknown piece at ", letter[i] + str(8 - j))
                    was_unknown_piece = True
        if empty_cells_counter > 0 and c == "-":
            s += str(empty_cells_counter)
            empty_cells_counter = 0

        if j != 7:
            s += r"/"

        # s += c
        # ss = ""
        # for i in range(8):

    # "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    s += " w KQkq - 0 1"
    if was_unknown_piece:
        return ""
    # print s
    return s


black_pieces = "r", "b", "k", "n", "p", "q"
white_pieces = "R", "B", "K", "N", "P", "Q"

# convert FEN to 2d list with user playing pieces
def FEN2board(FEN_string, play_white):

    if play_white:
        pieces = white_pieces
    else:
        pieces = black_pieces

    board = []
    x, y = 0, 0
    row = []
    for c in FEN_string:
        if c in pieces:
            row.append(c)
        elif c == "/":  # new line
            board.append(row)
            row = []
        elif c == " ":
            break
        elif c in ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9"):
            for i in range(int(c)):
                row.append("-")
        else:
            row.append("*")

    board.append(row)

    return board


def FENs2move(FEN_prev, FEN, play_white):
    print("---------------------- FENs2move() --------------------")
    print("FEN_prev=", FEN_prev, "FEN=", FEN)

    board_prev = FEN2board(FEN_prev, play_white)
    board = FEN2board(FEN, play_white)

    #    for i in range(8):
    #        for j in range(8):
    #            print board_prev[i][j],
    #        print

    #    print
    #    for i in range(8):
    #        for j in range(8):
    #            print board[i][j],
    #        print

    if play_white:
        pieces = white_pieces
    else:
        pieces = black_pieces

    p_from = {}
    p_to = {}
    for i in range(8):
        for j in range(8):
            if board[i][j] == "-" and board_prev[i][j] in pieces:
                #                print board_prev[i][j],"from",letter[j]+str(8-i)
                p_from[board_prev[i][j]] = letter[j] + str(8 - i)
            if board[i][j] in pieces and board_prev[i][j] not in pieces:
                #                print board[i][j],"to",letter[j]+str(8-i)
                p_to[board[i][j]] = letter[j] + str(8 - i)

    move = ""

    # test for conversion
    if play_white:
        pawn = "P"
        row = "7"
    else:
        pawn = "p"
        row = "2"

    if pawn in p_from:
        print("Movement", pawn)
        if row in p_from[pawn]:
            print("Found conversion !")
            for key in p_to:
                if key != pawn:
                    move = p_from[pawn] + p_to[key] + key
                    return move

    if "k" in p_from and "k" in p_to:
        #        print "Found k"
        move = p_from["k"] + p_to["k"]
    elif "K" in p_from and "K" in p_to:
        #        print "Found K"
        move = p_from["K"] + p_to["K"]
    else:
        for key in p_from:
            if key in p_to:
                move = p_from[key] + p_to[key]

    print("------------ move found:", move, "---------------")
    return move


class InvalidMove(Exception):
    pass


def get_moves(board, fen):
    """
    :param board:
    :type board: chess.Board
    :param fen:
    :param max_depth:
    :return:
    """
    board_fen = fen.split()[0]
    logging.debug('Getting diff between {} and {}'.format(board.board_fen(), board_fen))
    if board.board_fen() == board_fen:
        logging.debug('Positions identical')
        return []
    copy_board = board.copy()  # type: chess.Board
    moves = list(board.generate_legal_moves())
    for move in moves:
        copy_board.push(move)
        if board_fen == copy_board.board_fen():
            logging.debug('Single move detected - {}'.format(move.uci()))
            return [move.uci()]
        copy_board.pop()
    for move in moves:
        copy_board.push(move)
        legal_moves2 = list(copy_board.generate_legal_moves())
        for move2 in legal_moves2:
            copy_board.push(move2)
            if board_fen == copy_board.board_fen():
                logging.debug('Double move detected - {}, {}'.format(move.uci(), move2.uci()))
                return [move.uci(), move2.uci()]
            copy_board.pop()
        copy_board.pop()
    logging.debug('Unable to detect moves')
    raise InvalidMove()

