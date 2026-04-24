from .base_view import BaseViewPygame

import pygame
from core import Action, WIDTH, HEIGHT, SIZE

class Artist(BaseViewPygame):
    def __init__(self, screen=None, state=None) -> None:
        self.state = state
        if screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
            self.created_screen = True
        else:
            self.screen = screen
            self.created_screen = False
        self.running = True
        self.this_tick_actions = []

    def show(self):
        self.screen.fill('black')

        for p in self.state:
            pygame.draw.rect(self.screen, p.color, (p.x,p.y,SIZE,SIZE))

        pygame.display.flip()

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

    def quit(self):
        if self.created_screen:
            pygame.quit()
