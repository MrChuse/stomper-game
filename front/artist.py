from .base_view import BaseViewPygame

import pygame
import pygame.freetype
pygame.freetype.init()

from back.core import SquareMoveGame, Action, WIDTH, HEIGHT, SIZE

class Artist(BaseViewPygame):
    def __init__(self, screen=None, game: SquareMoveGame = None, tick_pos=None) -> None:
        self.game = game
        self.tick_pos = tick_pos
        if screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
            self.created_screen = True
        else:
            self.screen = screen
            self.created_screen = False
        self.running = True
        self.this_tick_actions = []
        self.time_delta = 0
        self.predicted_ticks = ''

        self.font = pygame.freetype.SysFont('Segoe Print', 30)

    def show(self):
        for p in self.game.players:
            pygame.draw.rect(self.screen, p.color, (p.x,p.y,SIZE,SIZE))

        self.font.render_to(self.screen, (*self.tick_pos, *(0, 0)), str(self.game.current_tick), 'white')
        if self.time_delta > 0:
            self.font.render_to(self.screen, (0, 30, 0, 0), str(round(self.time_delta, 2)) + ' ups', 'white')
        if self.predicted_ticks != '':
            self.font.render_to(self.screen, (0, 60, 0, 0), str(self.predicted_ticks) + ' it', 'white')

        self.this_tick_actions = []
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.this_tick_actions.append(Action.LEFT)
        if keys[pygame.K_RIGHT]:
            self.this_tick_actions.append(Action.RIGHT)
        if keys[pygame.K_UP]:
            self.this_tick_actions.append(Action.UP)
        if keys[pygame.K_DOWN]:
            self.this_tick_actions.append(Action.DOWN)

    def process_event(self, event):
        super().process_event(event)
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False

    def quit(self):
        if self.created_screen:
            pygame.quit()
