import argparse
import serial
from utils import find_port


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
    port = serial.Serial(portname, 38400, timeout=2.5)
    try:
        if args.all:
            if args.all == 'on':
                port.write('\xff' * 8)
            elif args.all == 'off':
                port.write('\x00' * 8)
    finally:
        port.close()


if __name__ == '__main__':
    main()