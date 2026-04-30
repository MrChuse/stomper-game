from dataclasses import dataclass
from enum import Enum
from random import randint, normalvariate
import itertools
import logging
from functools import singledispatchmethod
from math import ceil

import pygame

@dataclass
class Player:
    pos: pygame.Vector2
    color: pygame.Color
    vy: float = 0
    collides: bool = False
    grounded: bool = False
    holds_jump: bool = False

    def __init__(self, x, y, color):
        self.pos = pygame.Vector2(x, y)
        self.color = color


@dataclass
class Block:
    pos: pygame.Vector2

    @singledispatchmethod
    def __init__(self, x, y):
        self.pos = pygame.Vector2(x, y)

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
SIZE_TUP = (SIZE, SIZE)
BLOCK_SIZE = 30
BLOCK_SIZE_TUP = (BLOCK_SIZE, BLOCK_SIZE)
GRAVITY = 1
PLAYER_SPEED = 5
MAX_SPEED = BLOCK_SIZE / 3

BLOCKS_IN_ROW = ceil(WIDTH / BLOCK_SIZE)

class PlatformJumpGame:
    def __init__(self):
        self.current_tick = 0
        self.players: list[Player] = []
        self.blocks: list[Block] = []
        self.create_random_row(HEIGHT - BLOCK_SIZE)
        self.create_random_row(HEIGHT - BLOCK_SIZE * 5)
        self.create_random_row(HEIGHT - BLOCK_SIZE * 10)

    def create_block_range(self, start, length, height):
        print(f'create block range {start}, {length}, {height}')
        for i in range(length):
            self.blocks.append(Block(start, height))
            start += BLOCK_SIZE

    def create_random_row(self, height):
        created_blocks = 0
        current_type = randint(0, 1) # 1 is block, 0 is air
        while created_blocks < BLOCKS_IN_ROW:
            current_block_range = max(3, int(normalvariate(5, 3)))
            if created_blocks == 0 and current_block_range > BLOCKS_IN_ROW:
                self.create_block_range(0, BLOCKS_IN_ROW // 3, height)
                self.create_block_range(
                    WIDTH - (BLOCKS_IN_ROW // 3) * BLOCK_SIZE,
                    BLOCKS_IN_ROW // 3,
                    HEIGHT - BLOCK_SIZE
                )
                return
            
            if current_type == 1:
                current_block_range = min(current_block_range, BLOCKS_IN_ROW - created_blocks)
                self.create_block_range(created_blocks * BLOCK_SIZE, current_block_range, height)
            created_blocks += current_block_range
            current_type = 1 - current_type
            



    def create_random_player(self):
        logging.debug(f'creating random player on tick {self.current_tick}')
        p = random_player()
        self.players.append(p)

    def update(self, actions: dict[int, list[Action]]):
        logging.debug(f'core.update {self.current_tick} {actions}')
        highest_block = HEIGHT
        for b in self.blocks.copy():
            b.pos.y += 1
            highest_block = min(highest_block, b.pos.y)
            if b.pos.y >= HEIGHT:
                self.blocks.remove(b)

        if highest_block > BLOCK_SIZE * 4:
            self.create_random_row(-BLOCK_SIZE)

        for p_id, p_actions in actions.items():
            p = self.players[p_id]

            # actions
            up_this_turn = False
            for action in p_actions:
                if action is Action.LEFT:
                    p.pos.x -= PLAYER_SPEED
                    if p.pos.x < 0:
                        p.pos.x = 0
                if action is Action.RIGHT:
                    p.pos.x += PLAYER_SPEED
                    if p.pos.x > WIDTH - SIZE:
                        p.pos.x = WIDTH - SIZE
                if action is Action.UP:
                    up_this_turn = True
                    if (p.grounded or p.pos.y == HEIGHT - SIZE) or p.holds_jump:
                        p.holds_jump = True
                        p.vy = -10
                if action is Action.DOWN:
                    p.vy = max(p.vy, 2)
                    p.pos.y += p.vy
                    p.holds_jump = False
            if not up_this_turn:
                p.holds_jump = False

            # gravity
            p.vy += GRAVITY
            p.vy = min(MAX_SPEED, p.vy)
            p.pos.y += p.vy

            # floor clipping
            if p.pos.y > HEIGHT - SIZE:
                p.vy = 0
                p.pos.y = HEIGHT - SIZE
            if p.pos.y < 0:
                p.vy = 0
                p.pos.y = 0
                p.holds_jump = False

            # block collisions
            p.collides = False
            p.grounded = False
            for b in self.blocks:
                p_rect = pygame.Rect(p.pos, SIZE_TUP)
                b_rect = pygame.Rect(b.pos, BLOCK_SIZE_TUP)
                collides_this = p_rect.colliderect(b_rect)
                p.collides = p.collides or collides_this

                if collides_this:
                    dp = pygame.Vector2(p_rect.center) - pygame.Vector2(b_rect.center)
                    angle = dp.angle
                    # print(angle)
                    # collided from the bottom
                    if 45 < angle < 135:
                        if b_rect.centery < p_rect.top < b_rect.bottom:
                            p_rect.top = b_rect.bottom
                            p.vy = 0
                            p.holds_jump = False
                            
                    
                    # collided from the top
                    elif -135 < angle < -45:
                        if b_rect.top < p_rect.bottom < b_rect.centery:
                            p_rect.bottom = b_rect.top
                            p.vy = 0
                            p.grounded = True

                    # collided from the right
                    elif -45 < angle < 45:
                        if b_rect.left < p_rect.left < b_rect.right:
                            p_rect.left = b_rect.right
                    
                    # collided from the left
                    elif 135 < angle  or angle < -135:
                        if b_rect.left < p_rect.right < b_rect.right:
                            p_rect.right = b_rect.left

                    p.pos = pygame.Vector2(p_rect.topleft)


        self.current_tick += 1

    def to_list(self):
        res = [self.current_tick]
        for p in self.players:
            res.extend([p.pos.x, p.pos.y, p.vy, p.color.r, p.color.g, p.color.b])
        return res

    def to_bytes(self):
        l = ['state', str(self.current_tick)]
        for p in self.players:
            l.append(" ".join(map(str, (p.pos.x, p.pos.y, p.vy, p.color.r, p.color.g, p.color.b))))
        return " ".join(l).encode()
