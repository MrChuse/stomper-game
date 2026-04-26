import queue

import pygame

from core import Game
from server import Server, ServerPacket

class GameServerHeadless:
    def __init__(self):
        self.connection = Server()
        self.game = Game(True)

        self.clock = pygame.time.Clock()
        self.running = True

        self.received_packets: list[ServerPacket] = []
        self.current_tick_packets: list[ServerPacket] = []

    def update(self):
        try:
            while True:
                try:
                    packet = self.connection.packets_to_local.get(False)
                    self.received_packets.append(packet)
                except queue.Empty:
                    break
            
            for packet in self.received_packets.copy():
                if packet.tick == self.game.current_tick:
                    self.current_tick_packets.append(packet)
                    self.received_packets.remove(packet)
            
            actions_to_local = {}
            for packet in self.current_tick_packets:
                actions_to_local.update(packet.actions)

            if len(actions_to_local) == len(self.game.players):
                actions_to_remote = self.game.update(actions_to_local)
                for a in actions_to_remote:
                    self.connection.packets_to_remote.put(a)

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

if __name__ == '__main__':
    gsh = GameServerHeadless()
    gsh.loop()