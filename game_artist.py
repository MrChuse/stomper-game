import settings
if settings.PROFILER:
    import yappi

import queue
import time
from collections import deque
import logging

import pygame

from back.core import SquareMoveGame as Game
# from back.platform_game import PlatformJumpGame as Game
from front.artist import Artist
# from front.platform_artist import Artist
from utils import Thread

class GameArtist:
    def __init__(self, screen=None):
        self.game = Game()
        self.game.create_random_player()
        self.artist = Artist(screen, self.game)

        self.clock = pygame.time.Clock()
        self.running = True

        self.last_sent_tick_time = time.perf_counter()
        self.last_sent_tick_times = deque(maxlen=60)

        self.core_thread = Thread(self.loop)
        self.update_artist()

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
            actions = self.artist.this_tick_actions

            self.game.update({0: actions})

            cur_tick = time.perf_counter()
            td = cur_tick - self.last_sent_tick_time
            if td > 0:
                self.last_sent_tick_times.append(1/td)
                self.artist.time_delta = sum(self.last_sent_tick_times) / len(self.last_sent_tick_times)
            self.last_sent_tick_time = cur_tick

            self.clock.tick(settings.UPS)
        except KeyboardInterrupt:
            self.quit()
            raise

    def quit(self):
        self.artist.quit()
        self.running = False

    def loop(self):
        while self.running:
            self.update()

if __name__ == '__main__':
    if settings.PROFILER:
        yappi.start()
    logging.basicConfig(level=settings.LOGGING_LEVEL)
    gsa = GameArtist()
    if settings.PROFILER:
        yappi.get_func_stats().print_all()
        yappi.get_thread_stats().print_all()
        yappi.get_func_stats().save('profile/server.prof', 'pstat')
