from dataclasses import dataclass
from enum import Enum
from random import randint
import itertools

import pygame

@dataclass
class Player:
    x: float
    y: float
    color: pygame.Color

class Action(Enum):
    RIGHT = 0
    UP = 1
    LEFT = 2
    DOWN = 3
    CONNECT = 4
    DISCONNECT = 5
    STATE = 6

def random_color():
    return pygame.Color(randint(0, 255),randint(0, 255),randint(0, 255))

def random_player():
    return Player(randint(0, WIDTH-1-SIZE), randint(0, HEIGHT-1-SIZE), random_color())

WIDTH = 480
HEIGHT = 360
SIZE = 30
class Game:
    def __init__(self, is_server=True):
        self.current_tick = 0
        self.players: list[Player] = []
        self.is_server = is_server

    def create_random_player(self):
        # print(f'creating random player on tick {self.current_tick}')
        p = random_player()
        self.players.append(p)

    def update(self, actions: dict):
        # print('tick', self.current_tick)
        outgoing_actions = []
        for p_id, p_actions in actions.items():
            for action in p_actions:
                p = self.players[p_id]
                if action is Action.LEFT:
                    p.x -= 1
                if action is Action.RIGHT:
                    p.x += 1
                if action is Action.UP:
                    p.y -= 1
                if action is Action.DOWN:
                    p.y += 1
        self.current_tick += 1
        return outgoing_actions

    def to_list(self):
        res = [self.current_tick]
        for p in self.players:
            res.extend([p.x, p.y, p.color.r, p.color.g, p.color.b])
        return res

    def to_bytes(self):
        l = ['state', str(self.current_tick)]
        for p in self.players:
            l.append(" ".join(map(str, (p.x, p.y, p.color.r, p.color.g, p.color.b))))
        return " ".join(l).encode()
