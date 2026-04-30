from .base_view import BaseViewPygame

import pygame
import pygame.freetype
pygame.freetype.init()

from back.platform_game import PlatformJumpGame, Action, WIDTH, HEIGHT, SIZE, BLOCK_SIZE

class Artist(BaseViewPygame):
    def __init__(self, screen=None, game: PlatformJumpGame = None) -> None:
        self.game = game
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

        self.font = pygame.freetype.SysFont('Segoe Print', 30)

    def show(self):
        self.screen.fill('black')

        for p in self.game.players:
            if p.collides:
                color = 'red'
            else:
                color = p.color
            pygame.draw.rect(self.screen, color, (p.pos.x,p.pos.y,SIZE,SIZE))
        for b in self.game.blocks:
            pygame.draw.rect(self.screen, 'white', (b.pos.x, b.pos.y,BLOCK_SIZE, BLOCK_SIZE), width=1)

        self.font.render_to(self.screen, (0, 0, 0, 0), str(self.game.current_tick), 'white')
        if self.time_delta > 0:
            self.font.render_to(self.screen, (0, 30, 0, 0), str(round(self.time_delta, 2)) + ' ups', 'white')

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
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False

    def quit(self):
        if self.created_screen:
            pygame.quit()
