import os

import Queue
import logging
import re
import subprocess
import threading

from random import randint


class AsyncLineReader(threading.Thread):
    def __init__(self, fd, outputQueue):
        threading.Thread.__init__(self)

        assert isinstance(outputQueue, Queue.Queue)
        assert callable(fd.readline)

        self.fd = fd
        self.outputQueue = outputQueue

    def run(self):
        for line in iter(self.fd.readline, ""):
            logging.info("Engine: %s", line)
            self.outputQueue.put(line)

    def eof(self):
        return not self.is_alive() and self.outputQueue.empty()

    @classmethod
    def getForFd(cls, fd, start=True):
        queue = Queue.Queue()
        reader = cls(fd, queue)

        if start:
            reader.start()

        return reader, queue


class Engine(subprocess.Popen):
    """
    This initiates the Stockfish chess engine with Ponder set to False.
    'param' allows parameters to be specified by a dictionary object with 'Name' and 'value'
    with value as an integer.

    i.e. the following explicitly sets the default parameters
    {
        "Contempt Factor": 0,
        "Min Split Depth": 0,
        "Threads": 1,
        "Hash": 16,
        "MultiPV": 1,
        "Skill Level": 20,
        "Move Overhead": 30,
        "Minimum Thinking Time": 20,
        "Slow Mover": 80,
    }

    If 'rand' is set to False, any options not explicitly set will be set to the default
    value.

    -----
    USING RANDOM PARAMETERS
    -----
    If you set 'rand' to True, the 'Contempt' parameter will be set to a random value between
    'rand_min' and 'rand_max' so that you may run automated matches against slightly different
    engines.
    """

    def __init__(
        self,
        depth=2,
        ponder=False,
        param=None,
        rand=False,
        rand_min=-10,
        rand_max=10,
        rom='lyon16',
        chess960=False,
    ):
        dir_ = os.getcwd()
        os.chdir(os.path.join(os.getcwd(), 'engines', 'MessChess'))
        binary_path = ['MessChess.exe', rom]
        subprocess.Popen.__init__(
            self,
            binary_path,
            universal_newlines=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )
        os.chdir(dir_)
        self.output_queue = Queue.Queue()
        self.output_reader = AsyncLineReader(self.stdout, self.output_queue)
        self.output_reader.start()
        self.depth = depth
        self.ponder = ponder
        self.put("uci")
        if not ponder:
            self.setoption("Ponder", False)

        if param:
            base_param = param
        else:
            base_param = {
                "Write Debug Log": "false",
                "Contempt Factor": 0,  # There are some stockfish versions with Contempt Factor
                "Contempt": 0,  # and others with Contempt. Just try both.
                "Min Split Depth": 0,
                "Threads": 1,
                "Hash": 16,
                "MultiPV": 1,
                "Skill Level": 20,
                "Strength": 50,
                "Move Overhead": 30,
                "Minimum Thinking Time": 20,
                "Slow Mover": 80,
            }

        if rand:
            base_param["Contempt"] = (randint(rand_min, rand_max),)
            base_param["Contempt Factor"] = (randint(rand_min, rand_max),)

        self.param = base_param
        self.param["UCI_Chess960"] = "false" if not chess960 else "true"
        for name, value in list(self.param.items()):
            # print(name, value)
            self.setoption(name, value)

    def newgame(self):
        """
        Calls 'ucinewgame' - this should be run before a new game
        """
        self.put("ucinewgame")
        self.isready()

    def put(self, command):
        logging.info("Command: %s", command)
        self.stdin.write(command + "\n")
        self.stdin.flush()

    def flush(self):
        self.stdout.flush()

    def setoption(self, optionname, value):
        self.put("setoption name %s value %s" % (optionname, str(value)))
        stdout = self.isready()
        # Not working because self.isready() will only return readyok
        if stdout.find("No such") >= 0:
            print("stockfish was unable to set option %s" % optionname)

    def setposition(self, moves=(), starting_position=None):
        """
        Move list is a list of moves (i.e. ['e2e4', 'e7e5', ...]) each entry as a string.  Moves must be in full algebraic notation.
        """
        if starting_position:
            position = "fen {}".format(starting_position)
        else:
            position = "startpos"
        if moves:
            self.put("position {} moves {}".format(position, Engine._movelisttostr(moves)))
        else:
            self.put("position {}".format(position))
        self.isready()

    def setfenposition(self, fen):
        """
        set position in fen notation.  Input is a FEN string i.e. "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        """
        self.put("position fen %s" % fen)
        self.isready()

    def go(self):
        self.put("go depth %s" % self.depth)

    @staticmethod
    def _movelisttostr(moves):
        """
        Concatenates a list of strings.

        This is format in which stockfish "setoption setposition" takes move input.
        """
        return " ".join(moves)

    def trybestmove(self):
        try:
            text = self.output_queue.get_nowait()
        except Queue.Empty:
            return
        text = text.strip()
        split_text = text.split(" ")
        result = {}
        if split_text[0] == "info":
            last_info = Engine._bestmove_get_info(text)
            if "pv" not in last_info:
                logging.debug("No pv in last_info")
                return
            else:
                logging.debug("PV in last_info: %s", last_info["pv"])
                result = {"move": last_info["pv"].split()[0]}
            if "depth" not in last_info:
                logging.debug("Depth not found")
                return
            if last_info["depth"] > self.depth:
                result["depth"] = last_info["depth"]
            return result
        if split_text[0] == "bestmove":
            ponder = None if len(split_text) < 3 else split_text[2]
            return {"move": split_text[1], "ponder": ponder, "best_move": True}

    def bestmove(self):
        """
        Get proposed best move for current position.

        @return: dictionary with 'move', 'ponder', 'info' containing best move's UCI notation,
        ponder value and info dictionary.
        """
        self.go()
        last_info = ""
        while True:
            text = self.output_queue.get().strip()
            split_text = text.split(" ")
            logging.info("Got engine line: %s", text)
            # print(text)
            if split_text[0] == "info":
                last_info = Engine._bestmove_get_info(text)
                if "pv" not in last_info:
                    continue
            if split_text[0] == "bestmove":
                ponder = None if len(split_text) < 3 else split_text[2]
                return {"move": split_text[1], "ponder": ponder, "info": last_info}

    @staticmethod
    def _bestmove_get_info(text):
        """
        Parse stockfish evaluation output as dictionary.

        Examples of input:

        "info depth 2 seldepth 3 multipv 1 score cp -656 nodes 43 nps 43000 tbhits 0 \
        time 1 pv g7g6 h3g3 g6f7"

        "info depth 10 seldepth 12 multipv 1 score mate 5 nodes 2378 nps 1189000 tbhits 0 \
        time 2 pv h3g3 g6f7 g3c7 b5d7 d1d7 f7g6 c7g3 g6h5 e6f4"
        """
        result_dict = Engine._get_info_pv(text)
        result_dict.update(Engine._get_info_score(text))

        single_value_fields = [
            "depth",
            "seldepth",
            "multipv",
            "nodes",
            "nps",
            "tbhits",
            "time",
        ]
        for field in single_value_fields:
            result_dict.update(Engine._get_info_singlevalue_subfield(text, field))

        return result_dict

    @staticmethod
    def _get_info_singlevalue_subfield(info, field):
        """
        Helper function for _bestmove_get_info.

        Extracts (integer) values for single value fields.
        """
        search = re.search(pattern=field + " (?P<value>\d+)", string=info)
        if search:
            return {field: int(search.group("value"))}
        else:
            return {}

    @staticmethod
    def _get_info_score(info):
        """
        Helper function for _bestmove_get_info.

        Example inputs:

        score cp -100        <- engine is behind 100 centipawns
        score mate 3         <- engine has big lead or checkmated opponent
        """
        search = re.search(pattern="score (?P<eval>\w+) (?P<value>-?\d+)", string=info)
        if search:
            return {
                "score": {
                    "eval": search.group("eval"),
                    "value": int(search.group("value")),
                }
            }
        else:
            return {}

    @staticmethod
    def _get_info_pv(info):
        """
        Helper function for _bestmove_get_info.

        Extracts "pv" field from bestmove's info and returns move sequence in UCI notation.
        """
        search = re.search(pattern=PV_REGEX, string=info)
        if search:
            return {"pv": search.group("move_list")}
        else:
            return {}

    def isready(self):
        """
        Used to synchronize the python engine object with the back-end engine.  Sends 'isready' and waits for 'readyok.'
        """
        self.put("isready")
        while True:
            text = self.output_queue.get().strip()
            # print(text)
            if text == "readyok":
                return text


class RomEngine:
    def __init__(self, get_queue, send_queue, depth=2, rom='lyon16'):
        self.engine = Engine(depth=depth, rom=rom)
        self.engine.newgame()
        self.get_queue = get_queue
        self.send_queue = send_queue
        self.start()

    def start(self):
        while True:
            try:
                cmd, arg = self.get_queue.get_nowait()
            except Queue.Empty:
                continue
            if cmd == 'kill':
                print('Killing Engine')
                self.engine.kill()
                return
            elif cmd == 'move':
                # print('move:', arg)
                self.go(arg)
            else:
                print('Command not recognized')

    def go(self, move_list):
        self.engine.setposition(move_list)
        move = self.engine.bestmove()
        # print('got move', move)
        self.send_queue.put(move['move'])
        return

    def kill(self):
        self.engine.kill()


class RomEngineThread:
    def __init__(self, depth=2, rom='lyon16'):
        self.get_queue = Queue.Queue()
        self.send_queue = Queue.Queue()
        t = threading.Thread(target=RomEngine, args=(self.send_queue, self.get_queue, depth, rom))
        t.daemon = True
        t.start()
        self.best_move = None

    def send(self, cmd):
        self.send_queue.put(cmd)

    def kill(self):
        self.send(('kill', None))

    def go(self, move_list=[]):
        self.send_queue.put(('move', move_list))
        self.best_move = None

    def waiting_ai_move(self):
        if self.best_move:
            return False

        try:
            move = self.get_queue.get_nowait()
        except Queue.Empty:
            return True
        else:
            self.best_move = move
            return False

