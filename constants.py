import os


ENGINE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'engines')
DEFAULT_ENGINE = 'stockfish'

try:
    from local_constants import *
except ImportError:
    pass