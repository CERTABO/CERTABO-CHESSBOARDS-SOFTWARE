from constants import BASE_PORT


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