import argparse
import time
import subprocess
from utils import find_port, port2udp, port2number
from socket import AF_INET, SOCK_DGRAM, socket, SOL_SOCKET, SO_REUSEADDR, SO_BROADCAST


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('--port', type=int)
    p.add_argument('--all', default='on')
    return p.parse_args()


def main():
    args = parse_args()
    if args.port is None:
        portname = find_port()
    else:
        portname = args.port
    port = port2number(portname)
    board_listen_port, gui_listen_port = port2udp(port)

    SEND_SOCKET = ("127.0.0.1", board_listen_port)  # send to

    sock = socket(AF_INET, SOCK_DGRAM)
    sock.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

    usb_command = ["python", "usbtool.py"]
    if portname is not None:
        usb_command.extend(["--port", portname])
    usb_proc = subprocess.Popen(usb_command)
    time.sleep(1)

    message = None
    if args.all:
        if args.all == 'on':
            message = '\xff' * 8
        elif args.all == 'off':
            message = '\x00' * 8

    if message:
        sock.sendto(message, SEND_SOCKET)

    usb_proc.terminate()


if __name__ == '__main__':
    main()