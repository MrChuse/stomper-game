from dataclasses import dataclass
from enum import Enum
from random import randint
import queue

import pygame
import pygame.draw

from utils import Thread

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

def random_player():
    return Player(randint(0, WIDTH-1-SIZE), randint(0, HEIGHT-1-SIZE), random_color())

WIDTH = 1280
HEIGHT = 720
SIZE = 30
class Game:
    def __init__(self, connection):
        self.connection = connection
        self.running = True
        self.state: list[Player] = []
        self.update_thread = Thread(self.update)
    
    def update(self):
        while self.running:
            try:
                action = self.connection.actions_to_local.get()
            except queue.ShutDown:
                return
            # action handling
            p_id = action['player']
            if p_id < 0 or p_id >= len(self.state):
                if action['action'] is Action.CONNECT:
                    p = random_player()
                    self.state.append(p)
                continue
            p = self.state[action['player']]
            action = action['action']
            if action is Action.LEFT:
                p.x -= 1
            if action is Action.RIGHT:
                p.x += 1
            if action is Action.UP:
                p.y -= 1
            if action is Action.DOWN:
                p.y += 1
            if action is Action.DISCONNECT:
                self.state.pop(p_id)
                
    def quit(self):
        self.running = False
        pygame.quit()
        self.connection.quit()

    def main(self):
        # pygame setup
        pygame.init()
        screen = pygame.display.set_mode((WIDTH, HEIGHT))
        clock = pygame.time.Clock()

        while self.running:
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
            self.connection.add_actions(this_tick_actions)
            
            # draw
            screen.fill('black')

            # print(state)
            for p in self.state:
                pygame.draw.rect(screen, p.color, (p.x,p.y,SIZE,SIZE))

            # flip() the display to put your work on screen
            pygame.display.flip()

            clock.tick(60)  # limits FPS to 60

        self.quit()

    if __name__ == '__main__':
        main()