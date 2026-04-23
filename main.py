from dataclasses import dataclass
from enum import Enum
from random import randint

import pygame
import pygame.draw

@dataclass
class Player:
    x: float
    y: float
    color: pygame.color.ColorLike

class Action(Enum):
    RIGHT = 0
    UP = 1
    LEFT = 2
    DOWN = 3
    CONNECT = 4
    DISCONNECT = 5

def random_color():
    return pygame.Color(randint(0, 255),randint(0, 255),randint(0, 255))

SIZE = 30
class Game:
    def __init__(self, connection):
        self.connection = connection
    def main(self):
        # pygame setup
        pygame.init()
        screen = pygame.display.set_mode((1280, 720))
        clock = pygame.time.Clock()
        running = True

        state: list[Player] = []

        p = Player(100, 100, random_color())
        state.append(p)

        while running:
            # events and actions
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

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
            self.connection.add_actions(this_tick_actions)

            actions = self.connection.get_all_actions()
            # action handling
            for a in actions:
                p_id = a['player']
                if p_id < 0 or p_id >= len(state):
                    if a['action'] is Action.CONNECT:
                        p = Player(100, 100, random_color())
                    continue
                p = state[a['player']]
                action = a['action']
                if action is Action.LEFT:
                    p.x -= 1
                if action is Action.RIGHT:
                    p.x += 1
                if action is Action.UP:
                    p.y -= 1
                if action is Action.DOWN:
                    p.y += 1


            
            # draw
            screen.fill('black')

            for p in state:
                pygame.draw.rect(screen, p.color, (p.x,p.y,SIZE,SIZE))

            # flip() the display to put your work on screen
            pygame.display.flip()

            clock.tick(60)  # limits FPS to 60

        pygame.quit()
        self.connection.quit()

    if __name__ == '__main__':
        main()