import settings
if settings.PROFILER:
    import yappi

import queue
import time
from collections import deque
import logging

import pygame

from back.core import SquareMoveGame as Game
from front.artist import Artist
from server import Server, ServerPacket
from utils import Thread

class GameServerArtist:
    def __init__(self, host='', screen=None):
        self.connection = Server(host)
        self.connection.clients.append('local') # bad
        self.game = Game()
        self.game.create_random_player()
        self.connection.on_connect_callbacks.append(self.on_connect)
        self.connection.on_disconnect_callbacks.append(self.on_disconnect)
        self.artist = Artist(screen, self.game)

        self.clock = pygame.time.Clock()
        self.running = True

        self.received_packets: deque[ServerPacket] = deque(maxlen=settings.UPS)
        self.current_tick_packets: list[ServerPacket] = []

        self.last_sent_tick_time = time.perf_counter()
        self.last_sent_tick_times = deque(maxlen=60)

        self.core_thread = Thread(self.loop)
        self.update_artist()

    def on_connect(self):
        logging.info('on_connect called')
        self.game.create_random_player()
        self.connection.packets_to_remote.put({'state': self.game.to_bytes()})

    def on_disconnect(self, player_id):
        self.game.players.pop(player_id)

    def update_artist(self):
        clock = pygame.time.Clock()
        while self.running:
            pygame.display.set_caption(f'Stomper Game | {clock.get_fps():.1f}')
            self.artist.show()
            if self.artist.running is False:
                self.quit()
                return

            for event in pygame.event.get():
                self.artist.process_event(event)
            clock.tick(settings.FPS)

    def update(self):
        try:
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
                except queue.ShutDown:
                    self.quit()
                    return

            for packet in self.received_packets.copy():
                if packet.tick == self.game.current_tick:
                    self.current_tick_packets.append(packet)
                    self.received_packets.remove(packet)

            actions_to_local = {}
            for packet in self.current_tick_packets:
                actions_to_local.update(packet.actions)

            # print(actions_to_local, len(self.game.players))
            if len(actions_to_local) == len(self.game.players):
                self.game.update(actions_to_local)

                cur_tick = time.perf_counter()
                td = cur_tick - self.last_sent_tick_time
                if td > 0:
                    self.last_sent_tick_times.append(1/td)
                    self.artist.time_delta = sum(self.last_sent_tick_times) / len(self.last_sent_tick_times)
                self.last_sent_tick_time = cur_tick

                packet.actions.update(actions_to_local)
                self.connection.packets_to_remote.put(packet)

                self.current_tick_packets.clear()

            self.clock.tick(settings.UPS)
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
    gsa = GameServerArtist()
    if settings.PROFILER:
        yappi.get_func_stats().print_all()
        yappi.get_thread_stats().print_all()
        yappi.get_func_stats().save('profile/server.prof', 'pstat')
