import queue

import pygame

from main import Game, Artist
from client import Client

class GameClientArtist:
    def __init__(self):
        self.artist = Artist()
        self.connection = Client()
        self.game = Game(False)

        self.clock = pygame.time.Clock()
        self.running = True

    def update(self):
        state = self.game.state
        actions_to_remote = self.artist.draw(state)
        if self.artist.running is False:
            self.artist.quit()
            self.connection.quit()
            self.running = False
            return
        
        actions_to_local = []
        while True:
            try:
                action = self.connection.actions_to_local.get(False)
                actions_to_local.append(action)
            except queue.Empty:
                break
        
        actions = self.game.update(actions_to_local)
        actions_to_remote.extend(actions)
        for a in actions_to_remote:
            self.connection.actions_to_remote.put(a)
        
        self.clock.tick(60)
    
    def loop(self):
        while self.running:
            self.update()

gca = GameClientArtist()
gca.loop()