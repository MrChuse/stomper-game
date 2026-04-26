import queue

import pygame

from core import Game
from front.artist import Artist
from server import Server, ServerPacket

class GameServerArtist:
    def __init__(self, host='', screen=None):
        self.connection = Server(host)
        self.connection.clients.append('local') # bad
        self.game = Game(True)
        self.game.create_random_player()
        self.connection.on_connect_callbacks.append(self.on_connect)
        self.connection.on_disconnect_callbacks.append(self.on_disconnect)
        self.artist = Artist(screen, self.game)

        self.clock = pygame.time.Clock()
        self.running = True

        self.received_packets: list[ServerPacket] = []
        self.current_tick_packets: list[ServerPacket] = []

    def on_connect(self):
        self.game.create_random_player()
        self.connection.packets_to_remote.put({'state': self.game.to_bytes()})

    def on_disconnect(self, player_id):
        self.game.players.pop(player_id)

    def update(self):
        try:
            pygame.display.set_caption(f'Stomper Game | {self.clock.get_fps():.1f}')
            self.artist.show()
            if self.artist.running is False:
                self.artist.quit()
                self.connection.quit()
                self.running = False
                return

            for event in pygame.event.get():
                self.artist.process_event(event)
            actions_to_remote = self.artist.this_tick_actions

            packet = ServerPacket(self.game.current_tick)
            packet.actions[0] = actions_to_remote
            self.current_tick_packets.append(packet)

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
                self.game.update(actions_to_local)

                packet.actions.update(actions_to_local)
                self.connection.packets_to_remote.put(packet)

                self.current_tick_packets.clear()

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
    gsa = GameServerArtist()
    gsa.loop()