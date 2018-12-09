import logging
import os
import serial
from constants import BASE_PORT, ENGINE_PATH


if os.name == 'nt':  # sys.platform == 'win32':
    from serial.tools.list_ports_windows import comports
elif os.name == 'posix':
    from serial.tools.list_ports_posix import comports


def port2number(port):
    if isinstance(port, str):
        try:
            n = int(port)
        except ValueError:
            if isinstance(port, str):
                if port.upper().startswith('COM'):
                    return int(port[3:]) - 1  # Convert to zero based enumeration

        else:
            return n


def port2udp(port_number):
    if port_number is None:
        return BASE_PORT, BASE_PORT + 1
    board_listen_port = BASE_PORT + (port_number + 1) * 2
    gui_listen_port = board_listen_port + 1
    return board_listen_port, gui_listen_port


def find_port():
    logging.debug('Searching for port...')
    for port in comports():
        device = port[0]
        try:
            logging.debug('Trying %s', device)
            s = serial.Serial(device)
        except serial.SerialException:
            logging.debug('Port is busy, continuing...')
            continue
        else:
            s.close()
            logging.debug('Port is found! - %s', device)
            if isinstance(device, unicode):
                device = device.encode('utf-8')
            return device
    else:
        logging.debug('Port not found')
        return


def get_engine_list():
    result = []
    for filename in os.listdir(ENGINE_PATH):
        if filename.endswith('.exe'):
            result.append(filename[:-4])
    result.sort()
    return result


def coords_in(x, y, area):
    if not area:
        return False
    lx, ty, rx, by = area
    return lx < x < rx and ty < y < by