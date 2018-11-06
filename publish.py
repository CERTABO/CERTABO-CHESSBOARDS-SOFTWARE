import threading
import requests
import Queue
import time
import logging


PUBLISHER_SLEEP_INTERVAL = 0.1


class Publisher(threading.Thread):
    def __init__(self, url, queue, game_id=None, game_key=None):
        self.url = url
        self.game_id = game_id
        self.game_key = game_key
        if not self.url.endswith('/'):
            self.url += '/'
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
            data = {'pgn_data': message}
            try:
                if self.game_id:
                    url = '{}api/game/{}/'.format(self.url, self.game_id)
                    data['key'] = self.game_key
                    response = requests.patch(url, data=data)
                else:
                    url = '{}api/game/'.format(self.url)
                    response = requests.post(url, data=data)
            except requests.RequestException:
                logging.exception('Error publishing data to server')
            else:
                if not self.game_id:
                    data = response.json()
                    self.game_id = data['id']
                    self.game_key = data['key']

    def reset_game(self):
        self.game_id = None

    def stop(self):
        self.please_stop.set()