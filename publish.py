import threading
import requests
import Queue
import time
import logging


PUBLISHER_SLEEP_INTERVAL = 0.1


class Publisher(threading.Thread):
    def __init__(self, url, queue):
        self.url = url
        if not self.url.endswith('/'):
            self.url += '/'
        super(Publisher, self).__init__()
        self.queue = queue  # type: Queue.Queue
        self.please_stop = threading.Event()

    def run(self):
        game_id = None
        while not self.please_stop.is_set():
            try:
                message = self.queue.get_nowait()
            except Queue.Empty:
                time.sleep(PUBLISHER_SLEEP_INTERVAL)
                continue
            data = {'pgn_data': message}
            if game_id:
                data["id"] = game_id
                url = '{}api/game/{}/'.format(self.url, game_id)
            else:
                url = '{}api/game/'.format(self.url)
            try:
                response = requests.post(url, data=data)
            except requests.RequestException:
                logging.warning('Error publishing data to server')
            else:
                data = response.json()
                game_id = data['id']

    def stop(self):
        self.please_stop.set()