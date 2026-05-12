import settings
if settings.PROFILER:
    import yappi

import queue
import itertools
import time
from collections import deque
import logging
from copy import deepcopy
from threading import Lock

import pygame

from back.core import SquareMoveGame as Game, Player, WIDTH
from front.artist import Artist
from client import Client, ClientTickActions, ClientPacket
from server import ServerPacket
from utils import Thread

class GameClientArtist:
    def __init__(self, host='localhost', screen: pygame.Surface=None):
        self.screen = screen

        self.connection = Client(host)
        self.player_id = None
        self.connection.on_disconnect_callbacks.append(self.on_disconnect)

        self.server_state = Game()
        self.artist = Artist(screen, self.server_state, (WIDTH//2, 0))
        self.show_server_state = True

        self.predicted_state = deepcopy(self.server_state)
        self.predicted_artist = Artist(screen, self.predicted_state, (0, 0))
        self.predicted_lock = Lock()
        self.target_buffer_size = 35

        self.clock = pygame.time.Clock()
        self.running = True

        self.sent_packets: deque[ClientTickActions] = deque()
        self.received_packets: deque[ServerPacket] = deque(maxlen=100)
        self.current_tick_packets: list[ServerPacket] = []
        self.last_sent_tick_time = time.perf_counter()
        self.last_sent_tick_times = deque(maxlen=60)

        self.core_thread = Thread(self.loop)
        self.send_actions_thread = Thread(self.send_actions_loop)
        self.update_artist()

    def on_disconnect(self, player_id):
        self.server_state.players.pop(player_id)

    def copy_server_state(self):
        self.predicted_state = deepcopy(self.server_state)
        self.predicted_artist.game = self.predicted_state
        # logging.debug(f'copied server state to {self.predicted_state.current_tick}')

    def update_artist(self):
        clock = pygame.time.Clock()
        while self.running:
            # print('updating artist')
            pygame.display.set_caption(f'Stomper Game | {clock.get_fps():.1f}')
            # print('set caption')
            self.screen.fill('black')
            if self.show_server_state:
                 self.artist.show()
            with self.predicted_lock:
                self.predicted_artist.show()
            pygame.display.flip()
            # print('shown')
            if self.artist.running is False:
                self.quit()
                # print('quit')
                return
            # print('start handling events')
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                     if event.key == pygame.K_s:
                          self.show_server_state = not self.show_server_state
                self.artist.process_event(event)
            # print('end handling events')
            clock.tick(settings.FPS)

    def send_actions_loop(self):
        clock = pygame.time.Clock()
        while self.running:
            if len(self.sent_packets) < settings.UPS * 3:

                # this slows down the game if there's too many packets in queue and speeds up if too few
                # this tries to set the queue size to settings.UPS. Probably need a way to make this buffer as little as possible
                actual_ups = 2 * self.target_buffer_size - len(self.sent_packets)
                with self.predicted_lock:
                    self.send_actions()
                    # print(f'in send_actions loop {self.predicted_state.current_tick}')
                    if self.player_id is not None:
                        self.predicted_state.update({self.player_id: self.predicted_artist.this_tick_actions})
                    clock.tick(actual_ups)

    def collect_packets(self):
            # collects packets into self.received_packets
            # while True:
                try:
                    # packet = self.connection.packets_to_local.get(timeout=1)
                    # print('waiting for packet')
                    packet = self.connection.packets_to_local.get()
                    if isinstance(packet, dict):
                        if 'state' in packet:
                            with self.predicted_lock:
                                s = packet['state']
                                s = list(map(int, s))
                                logging.info(f'State: {s}')
                                if (len(s)-1) % 5 != 0:
                                    print("State was transferred wrong probably")
                                    # continue
                                self.server_state.current_tick = int(s[0])
                                self.server_state.players.clear()
                                for b in itertools.batched(s[1:], 5):
                                    self.server_state.players.append(Player(b[0], b[1], pygame.Color(b[2], b[3], b[4])))
                                logging.debug(f'set current_tick to {self.server_state.current_tick} in state transfer')
                                self.copy_server_state()
                                # self.send_actions()
                        elif 'player_id' in packet:
                             self.player_id = packet['player_id']
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
                if packet.tick == self.server_state.current_tick:
                    self.current_tick_packets.append(packet)
                    self.received_packets.remove(packet)
            # print(self.current_tick_packets)

            actions_to_local = {}
            for packet in self.current_tick_packets:
                actions_to_local.update(packet.actions)
            return actions_to_local

    def send_actions(self):
            try:
                if len(self.sent_packets) > 0:
                    already_sent_packet_for_this_tick = self.predicted_state.current_tick <= self.sent_packets[-1].tick
                    if already_sent_packet_for_this_tick:
                        return
                logging.debug(f'put {self.predicted_state.current_tick} to packets_to_remote')
                tick_actions = ClientTickActions(self.predicted_state.current_tick)
                tick_actions.actions.extend(self.predicted_artist.this_tick_actions)
                self.sent_packets.append(tick_actions)

                client_packet = ClientPacket(list(self.sent_packets))
                self.connection.packets_to_remote.put(client_packet)
            except queue.ShutDown:
                self.quit()

    def update(self):
        try:
            self.collect_packets()
            actions_to_local = self.parse_packets()
            logging.debug(f'{actions_to_local}, {len(self.server_state.players)}')

            all_good = True
            for i in range(len(self.server_state.players)):
                if i not in actions_to_local:
                    all_good = False
            if all_good:
                with self.predicted_lock:
                    self.server_state.update(actions_to_local)
                    self.copy_server_state()

                    earliest_packet = None
                    earliest_tick = -1
                    # print(self.sent_packets)
                    while earliest_tick < self.server_state.current_tick-1 and len(self.sent_packets) > 0:
                        earliest_packet = self.sent_packets.popleft()
                        earliest_tick = earliest_packet.tick
                    if earliest_packet and earliest_packet.tick == self.server_state.current_tick-1:
                        for packet in self.sent_packets:
                            actions = packet.actions
                            # print(f'in predict loop: {self.predicted_state.current_tick}, {packet.tick}')
                            if self.player_id is not None:
                                # logging.debug(f'applying packet {packet.tick} to state {self.predicted_state.current_tick}')
                                self.predicted_state.update({self.player_id: actions})
                        self.predicted_artist.predicted_ticks = len(self.sent_packets)
                        # if len(self.sent_packets) > 0:
                        #     logging.debug(f"Simulated up to the tick {packet.tick}. Current tick: {self.predicted_state.current_tick}")
                cur_tick = time.perf_counter()
                td = cur_tick - self.last_sent_tick_time
                if td > 0:
                    self.last_sent_tick_times.append(1/td)
                    self.predicted_artist.time_delta = sum(self.last_sent_tick_times) / len(self.last_sent_tick_times)
                self.last_sent_tick_time = cur_tick
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
    gca = GameClientArtist()
    if settings.PROFILER:
        yappi.get_func_stats().print_all()
        yappi.get_thread_stats().print_all()
        yappi.get_func_stats().save('profile/client.prof', 'pstat')