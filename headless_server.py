import queue

import pygame

from main import Game
from server import Server

class GameServerHeadless:
    def __init__(self):
        self.connection = Server()
        self.game = Game(True)

        self.clock = pygame.time.Clock()
        self.running = True

    def update(self):
        try:
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
            self.connection.quit()
            raise
    
    def loop(self):
        while self.running:
            self.update()

gsh = GameServerHeadless()
gsh.loop()