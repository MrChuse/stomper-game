import queue

import pygame

from main import Game, Artist
from server import Server

class GameServerArtist:
    def __init__(self):
        self.connection = Server()
        self.connection.clients.append('local') # bad
        self.game = Game(True)
        self.game.create_random_player()
        self.artist = Artist()

        self.clock = pygame.time.Clock()
        self.running = True

    def update(self):
        try:
            state = self.game.state
            actions_to_remote = self.artist.draw(state)
            if self.artist.running is False:
                self.artist.quit()
                self.connection.quit()
                self.running = False
                return

            for a in actions_to_remote:
                self.connection.actions_to_local.put({'player': 0, 'action': a})
                self.connection.actions_to_remote.put({'player': 0, 'action': a})

            actions_to_local = []
            while True:
                try:
                    action = self.connection.actions_to_local.get(False)
                    actions_to_local.append(action)
                except queue.Empty:
                    break

                

            actions_to_remote = self.game.update(actions_to_local)
            for a in actions_to_remote:
                self.connection.actions_to_remote.put(a)

            self.clock.tick(60)
        except KeyboardInterrupt:
            self.quit()
            raise

    def quit(self):
        self.connection.quit()
        self.running = False

    def loop(self):
        while self.running:
            self.update()

gsa = GameServerArtist()
gsa.loop()