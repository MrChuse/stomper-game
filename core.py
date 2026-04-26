from dataclasses import dataclass
from enum import Enum
from random import randint
import itertools

import pygame
import pygame.draw

@dataclass
class Player:
    x: float
    y: float
    color: pygame.color

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
        p = random_player()
        self.players.append(p)

    def update(self, actions):
        outgoing_actions = []

        for action in actions:
            if 'state' in action:
                if len(action['state']) % 5 != 0:
                    print("State was transferred wrong probably")
                    continue
                self.players.clear()
                for b in itertools.batched(action['state'], 5):
                    b = list(map(int, b))
                    self.players.append(Player(b[0], b[1], pygame.Color(b[2], b[3], b[4])))
            else:
                p_id = action['player']
                if p_id < 0 or p_id >= len(self.players):
                    if action['action'] is Action.CONNECT:
                        if self.is_server:
                            self.create_random_player()
                            outgoing_actions.append({'state': self.to_bytes()})
                    continue

                p = self.players[action['player']]
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
                    self.players.pop(p_id)
        self.current_tick += 1
        return outgoing_actions

    def to_bytes(self):
        l = ['state']
        for p in self.players:
            l.append(" ".join(map(str, (p.x, p.y, p.color.r, p.color.g, p.color.b))))
        return " ".join(l).encode()
