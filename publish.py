import threading
import requests
import Queue
import time
import logging


PUBLISHER_SLEEP_INTERVAL = 0.1


class Publisher(threading.Thread):
    def __init__(self, url, queue):
        self.url = url
        super(Publisher, self).__init__()
        self.queue = queue  # type: Queue.Queue
        self.please_stop = threading.Event()

    def run(self):
        while not self.please_stop.is_set():
            try:
                message = self.queue.get_nowait()
            except Queue.Empty:
                time.sleep(PUBLISHER_SLEEP_INTERVAL)
                continue
            try:
                requests.post(self.url, data={'pgn': message})
            except requests.RequestException:
                logging.warning('Error publishing data to server')

    def stop(self):
        self.please_stop.set()