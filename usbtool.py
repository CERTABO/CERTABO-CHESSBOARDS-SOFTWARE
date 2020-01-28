# TODO: Gracefully close port when exiting main App
# TODO: Kill app after x time
from __future__ import print_function
import serial.tools.list_ports

import sys

# for exe compile run python 1.py py2exe
import argparse
import time
from select import *
from socket import *
from utils import port2udp, port2number

DEBUG = False

print("--- usbtool started ---")

parser = argparse.ArgumentParser()
parser.add_argument('--port')
args = parser.parse_args()
if args.port:
    print('Got port argument', args.port)
else:
    print('No port argument speicified')

board_listen_port, gui_listen_port = port2udp(port2number(args.port))
print('USBTOOL: Board listen port: %s, gui listen port: %s' % (board_listen_port, gui_listen_port))

serial_ok = False
try:
    serial_port = serial.Serial(args.port, 38400, timeout=2.5)  # 0-COM1, 1-COM2 / speed /
    serial_ok = True
    serial_port.flushInput()
except Exception as e:
    print("Cannot open Serial at ", args.port)
    print(str(e))

if not serial_ok:
    try:
        serial_port = serial.Serial(args.port, 38400, timeout=2.5)  # 0-COM1, 1-COM2 / speed /
        serial_ok = True
        serial_port.flushInput()
    except Exception as e:
        print("Cannot open Serial at ", args.port)
        print(str(e))
        exit(1)

print("Started usbtool. waiting for new messages")

SEND_SOCKET = ("127.0.0.1", gui_listen_port)  # send to
LISTEN_SOCKET = ("127.0.0.1", board_listen_port)  # listen to
sock = socket(AF_INET, SOCK_DGRAM)
sock.bind(LISTEN_SOCKET)
sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)
recv_list = [sock]

message = ""
while True:
    time.sleep(0.001)

    # Try to reconnect to board
    if not serial_ok:
        try:
            serial_port = serial.Serial(args.port, 38400, timeout=2.5)
            serial_ok = True
            serial_port.flushInput()
        except Exception as e:
            print("Cannot open Serial at ", args.port)
            print(str(e))
            continue

    # Send message to board (leds)
    recv_ready, wtp, xtp = select(recv_list, [], [], 0.001)
    if recv_ready:
        try:
            data, addr = sock.recvfrom(2048)
        except error as e:
            print('Socket closed ungracefully before:', str(e))
            continue

        try:
            serial_port.write(data)
            if DEBUG:
                print("sending to usb data with length =", len(data))
        except Exception as e:
            print('Could not write to Serial port:', str(e))
            serial_ok = False
            continue

    # Read message from board (FEN)
    try:
        while serial_port.inWaiting():

            #if (sys.version_info.major == 3):
            if True:
                message = serial_port.readline().decode("ascii")
                # print(message)
                message = message[1: -3]
                # print(message)
                if DEBUG:
                    print(len(message.split(" ")), "numbers")
                if len(message.split(" ")) == 320:  # 64*5
                    sock.sendto(message.encode(), SEND_SOCKET)

                message = ""
            else:
                c = serial_port.read()

                if not c == '\n':
                    message += c
                else:
                    print(message)
                    message = message[1: -2]
                    print(message)
                    serial_port.flushInput()

                    if DEBUG:
                        print(len(message.split(" ")), "numbers")

                    if len(message.split(" ")) == 320:  # 64*5
                        sock.sendto(message, SEND_SOCKET)

                    message = ""
    except Exception as e:
        print('Failed to read from Serial port ', str(e))
        serial_ok = False
