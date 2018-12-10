import argparse
import time
import subprocess
from utils import find_port, port2udp, port2number
from socket import AF_INET, SOCK_DGRAM, socket, SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST
import chess
import struct
import binhex


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--port', type=int)
    p.add_argument('--all')
    p.add_argument('--on', nargs='+')
    return p.parse_args()


def main():
    args = parse_args()
    if args.port is None:
        portname = find_port()
    else:
        portname = args.port
    port = port2number(portname)
    usb_command = ["python", "usbtool.py"]
    if portname is not None:
        usb_command.extend(["--port", portname])
    usb_proc = subprocess.Popen(usb_command)
    time.sleep(3)

    board_listen_port, gui_listen_port = port2udp(port)

    SEND_SOCKET = ("127.0.0.1", board_listen_port)  # send to

    sock = socket(AF_INET, SOCK_DGRAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

    message = None
    if args.all:
        if args.all == 'on':
            message = '\xff' * 8
        elif args.all == 'off':
            message = '\x00' * 8
    elif args.on:
        square_set = chess.SquareSet()
        for arg in args.on:
            if len(arg) == 1:
                if arg in chess.FILE_NAMES:
                    file_index = chess.FILE_NAMES.index(arg)
                    square_set |= chess.BB_FILES[file_index]
                if arg in chess.RANK_NAMES:
                    rank_index = chess.FILE_NAMES.index(arg)
                    square_set |= chess.BB_RANKS[rank_index]
            elif len(arg) == 2:
                if arg in chess.SQUARE_NAMES:
                    square_index = chess.SQUARE_NAMES.index(arg)
                    square_set |= chess.BB_SQUARES[square_index]
        message = struct.pack('Q', int(square_set))

    if message:
        print('Sending %s', ' '.join(str(ord(c)) for c in message))
        sock.sendto(message, SEND_SOCKET)

    usb_proc.terminate()


if __name__ == '__main__':
    main()