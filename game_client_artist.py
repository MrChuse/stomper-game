import settings
if settings.PROFILER:
    import yappi

import queue
import itertools
import time
from collections import deque
import logging

import pygame

from core import Game, Player
from front.artist import Artist
from client import Client, ClientPacket
from server import ServerPacket
from utils import Thread

class GameClientArtist:
    def __init__(self, host='localhost', screen=None):
        self.connection = Client(host)
        self.game = Game(False)
        self.artist = Artist(screen, self.game)

        self.clock = pygame.time.Clock()
        self.running = True

        self.received_packets: deque[ServerPacket] = deque(maxlen=100)
        self.current_tick_packets: list[ServerPacket] = []
        self.last_sent_tick = -1
        self.last_sent_tick_time = time.perf_counter()
        self.last_sent_tick_times = deque(maxlen=60)

        self.core_thread = Thread(self.loop)
        self.update_artist()


    def update_artist(self):
        clock = pygame.time.Clock()
        while self.running:
            # print('updating artist')
            pygame.display.set_caption(f'Stomper Game | {clock.get_fps():.1f}')
            # print('set caption')
            self.artist.show()
            # print('shown')
            if self.artist.running is False:
                self.quit()
                # print('quit')
                return
            # print('start handling events')
            for event in pygame.event.get():
                self.artist.process_event(event)
            # print('end handling events')
            clock.tick(settings.FPS)

    def collect_packets(self):
            # collects packets into self.received_packets
            # while True:
                try:
                    # packet = self.connection.packets_to_local.get(timeout=1)
                    # print('waiting for packet')
                    packet = self.connection.packets_to_local.get()
                    if isinstance(packet, dict):
                        if 'state' in packet:
                            s = packet['state']
                            s = list(map(int, s))
                            logging.info(f'State: {s}')
                            if (len(s)-1) % 5 != 0:
                                print("State was transferred wrong probably")
                                # continue
                            self.game.current_tick = int(s[0])
                            self.game.players.clear()
                        for b in itertools.batched(s[1:], 5):
                            self.game.players.append(Player(b[0], b[1], pygame.Color(b[2], b[3], b[4])))
                        # print(f'set current_tick to {self.game.current_tick} in state transfer')
                        self.send_actions()
                    else:
                        # print(f'put {packet.tick} into received packets')
                        self.received_packets.append(packet)
                        
                except queue.Empty:
                    # break
                    logging.error('queue.Empty: This should be impossible')
                except queue.ShutDown:
                    self.quit()
                    return

    def parse_packets(self):
            # print(f'parsing packets on tick {self.game.current_tick}')
            for packet in self.received_packets.copy():
                # print(repr(packet.tick), repr(self.game.current_tick))
                if packet.tick == self.game.current_tick:
                    self.current_tick_packets.append(packet)
                    self.received_packets.remove(packet)
            # print(self.current_tick_packets)

            actions_to_local = {}
            for packet in self.current_tick_packets:
                actions_to_local.update(packet.actions)
            return actions_to_local

    def send_actions(self):
                packet_to_remote = ClientPacket(self.game.current_tick)
                packet_to_remote.actions.extend(self.artist.this_tick_actions)
                self.connection.packets_to_remote.put(packet_to_remote)
                self.last_sent_tick = self.game.current_tick

    def update(self):
        try:
            # print('tick', self.game.current_tick)


            if self.last_sent_tick < self.game.current_tick:
                self.send_actions()
            
            self.collect_packets()
            actions_to_local = self.parse_packets()
            logging.debug(f'{actions_to_local}, {len(self.game.players)}')

            if len(actions_to_local) == len(self.game.players):
                self.game.update(actions_to_local)
                cur_tick = time.perf_counter()
                td = cur_tick - self.last_sent_tick_time
                if td > 0:
                    self.last_sent_tick_times.append(1/td)
                    self.artist.time_delta = sum(self.last_sent_tick_times) / len(self.last_sent_tick_times)
                self.last_sent_tick_time = cur_tick
                self.current_tick_packets.clear()

            # self.clock.tick(1)
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
    if settings.PROFILER:
        yappi.start()
    logging.basicConfig(level=settings.LOGGING_LEVEL)
    gca = GameClientArtist()
    if settings.PROFILER:
        yappi.get_func_stats().print_all()
        yappi.get_thread_stats().print_all()
        yappi.get_func_stats().save('profile/client.prof', 'pstat')