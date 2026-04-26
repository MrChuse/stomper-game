import queue
import itertools

import pygame

from core import Game, Player
from front.artist import Artist
from client import Client, ClientPacket
from server import ServerPacket

class GameClientArtist:
    def __init__(self, host='localhost', screen=None):
        self.connection = Client(host)
        self.game = Game(False)
        self.artist = Artist(screen, self.game)

        self.clock = pygame.time.Clock()
        self.running = True

        self.received_packets: list[ServerPacket] = []
        self.current_tick_packets: list[ServerPacket] = []
        self.last_sent_tick = -1

    def update(self):
        try:
            # print('tick', self.game.current_tick)
            self.artist.show()
            if self.artist.running is False:
                self.quit()
                return

            for event in pygame.event.get():
                self.artist.process_event(event)

            state = None
            while True:
                try:
                    packet = self.connection.packets_to_local.get(False)
                    if isinstance(packet, dict):
                        if 'state' in packet:
                            s = packet['state']
                            print(s)
                            if (len(s)-1) % 5 != 0:
                                print("State was transferred wrong probably")
                                continue
                            self.game.current_tick = int(s[0])
                            self.game.players.clear()
                        for b in itertools.batched(s[1:], 5):
                            b = list(map(int, b))
                            self.game.players.append(Player(b[0], b[1], pygame.Color(b[2], b[3], b[4])))
                        print(f'set current_tick to {self.game.current_tick} in state transfer')
                    else:
                        self.received_packets.append(packet)
                        
                except queue.Empty:
                    break
                except queue.ShutDown:
                    self.quit()
                    return

            if self.last_sent_tick < self.game.current_tick:
                packet_to_remote = ClientPacket(self.game.current_tick)
                packet_to_remote.actions.extend(self.artist.this_tick_actions)
                self.connection.packets_to_remote.put(packet_to_remote)
                self.last_sent_tick = self.game.current_tick

            # print(self.game.current_tick)
            for packet in self.received_packets.copy():
                # print(repr(packet.tick), repr(self.game.current_tick))
                if packet.tick == self.game.current_tick:
                    self.current_tick_packets.append(packet)
                    self.received_packets.remove(packet)
            # print(self.current_tick_packets)

            actions_to_local = {}
            for packet in self.current_tick_packets:
                actions_to_local.update(packet.actions)
            if len(actions_to_local) == len(self.game.players):
                self.game.update(actions_to_local)

                self.current_tick_packets.clear()

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