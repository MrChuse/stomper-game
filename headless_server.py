import settings

import queue
from collections import deque
import logging

import pygame

from back.core import SquareMoveGame as Game
from server import Server, ServerPacket

class GameServerHeadless:
    def __init__(self):
        self.connection = Server()
        self.game = Game()

        self.connection.on_connect_callbacks.append(self.on_connect)
        self.connection.on_disconnect_callbacks.append(self.on_disconnect)

        self.clock = pygame.time.Clock()
        self.running = True

        self.received_packets: deque[ServerPacket] = deque(maxlen=settings.UPS)
        self.current_tick_packets: list[ServerPacket] = []

        self.loop()

    def on_connect(self):
        logging.info('on_connect called')
        self.game.create_random_player()
        self.connection.packets_to_remote.put({'state': self.game.to_bytes()})

    def on_disconnect(self, player_id):
        self.game.players.pop(player_id)

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

            # logging.debug(f'{actions_to_local}, {len(self.game.players)}')
            if len(actions_to_local) == len(self.game.players):
                logging.debug(f'update, {self.game.current_tick}')
                self.game.update(actions_to_local)
                self.current_tick_packets = []
                if len(self.game.players) > 0:
                    packet = ServerPacket(self.game.current_tick)
                    packet.actions.update(actions_to_local)
                    self.connection.packets_to_remote.put(packet)

            self.clock.tick(settings.UPS)
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