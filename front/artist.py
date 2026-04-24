from .base_view import BaseViewPygame

import pygame
from core import Action, WIDTH, HEIGHT, SIZE

class Artist(BaseViewPygame):
    def __init__(self, screen=None) -> None:
        if screen is None:
            pygame.init()
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
            self.created_screen = True
        else:
            self.screen = screen
            self.created_screen = False
        self.running = True

    def draw(self, state):
        # print('draw')
        self.screen.fill('black')

        for p in state:
            pygame.draw.rect(self.screen, p.color, (p.x,p.y,SIZE,SIZE))

        # flip() the display to put your work on screen
        pygame.display.flip()
        
        # events and actions
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

        this_tick_actions = []
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            this_tick_actions.append(Action.LEFT)
        if keys[pygame.K_RIGHT]:
            this_tick_actions.append(Action.RIGHT)
        if keys[pygame.K_UP]:
            this_tick_actions.append(Action.UP)
        if keys[pygame.K_DOWN]:
            this_tick_actions.append(Action.DOWN)
        return this_tick_actions

    def quit(self):
        if self.created_screen:
            pygame.quit()
