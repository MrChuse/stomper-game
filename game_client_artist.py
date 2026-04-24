import queue

import pygame

from core import Game
from front.artist import Artist
from client import Client

class GameClientArtist:
    def __init__(self, host='localhost', screen=None):
        self.connection = Client(host)
        self.game = Game(False)
        self.artist = Artist(screen, self.game.state)

        self.clock = pygame.time.Clock()
        self.running = True

    def update(self):
        try:
            self.artist.show()
            if self.artist.running is False:
                self.quit()
                return

            for event in pygame.event.get():
                self.artist.process_event(event)
            actions_to_remote = self.artist.this_tick_actions

            actions_to_local = []
            while True:
                try:
                    action = self.connection.actions_to_local.get(False)
                    actions_to_local.append(action)
                except queue.Empty:
                    break
                except queue.ShutDown:
                    self.quit()
                    return

            actions = self.game.update(actions_to_local)
            actions_to_remote.extend(actions)
            for a in actions_to_remote:
                self.connection.actions_to_remote.put(a)

            self.clock.tick(60)
        except KeyboardInterrupt:
            self.quit()
            raise

    def quit(self):
        self.artist.quit()
        self.connection.quit()
        self.running = False

    def loop(self):
        while self.running:
            self.update()

if __name__ == '__main__':
    gca = GameClientArtist()
    gca.loop()