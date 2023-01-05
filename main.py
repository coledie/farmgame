import sys
import numpy as np
import pygame
from pygame.locals import *


START_MAP = np.zeros((12, 16))
START_MAP[:, -2:] = 999
START_ITEM_MAP = np.zeros((12, 16))
START_ITEM_MAP[:, 0] = 10
START_ITEM_MAP[:, 1] = 11

image_map = {
    -1: "hole.png",
    0: "sand.png",
}

image_state_map = {
    0: "blank.png",
    1: "seed.png",
    2: "seedling.png",
    3: "flower.png",
    10: "stone.png",
    11: "tree.png",
}


tile_map = [[None for _ in range(START_MAP.shape[1])] for _ in range(START_MAP.shape[0])]
money = 20


def get_pos(x, y):
    return (x * 32 + 32, y * 32 + 32)


class Character(pygame.sprite.Sprite):
    """The Main Character"""
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.x, self.y = (8, 6)

        self.image = pygame.image.load("character.png")
        self.rect = self.image.get_rect()
        self.rect.update(get_pos(self.x, self.y), self.rect.size)

    def update(self):
        pass

    def tick(self):
        self.rect.update(get_pos(self.x, self.y), self.rect.size)

    def _check_safe_move(self, next_tile):
        return next_tile.water_level or next_tile.item.state

    def go_up(self):
        if not self.y:
            return
        next_tile = tile_map[self.y-1][self.x]
        if self._check_safe_move(next_tile):
            return
        self.y -= 1

    def go_down(self):
        if self.y == START_MAP.shape[0] - 1:
            return
        next_tile = tile_map[self.y+1][self.x]
        if self._check_safe_move(next_tile):
            return
        self.y += 1

    def go_left(self):
        if not self.x:
            return
        next_tile = tile_map[self.y][self.x-1]
        if self._check_safe_move(next_tile):
            return
        self.x -= 1

    def go_right(self):
        if self.x == START_MAP.shape[1] - 1:
            return
        next_tile = tile_map[self.y][self.x+1]
        if self._check_safe_move(next_tile):
            return
        self.x += 1


class Item(pygame.sprite.Sprite):
    """
    One item per tile    
    """
    def __init__(self, tile):
        pygame.sprite.Sprite.__init__(self)
        self.tile = tile

        self.state = START_ITEM_MAP[tile.y, tile.x]
        self.ticks_since_last_update = 0

        self.tick()
        self.rect = self.image.get_rect()
        self.rect.update((self.tile.rect.left, self.tile.rect.top), self.rect.size)

    def update(self):
        global money
        if self.state in [1, 2, 3]:
            self.ticks_since_last_update += 1
            if self.ticks_since_last_update == 60:
                self.ticks_since_last_update = 0
                self.state += 1
                if self.state == 4:
                    money += 10
                    self.state = 0
            if self.tile.water_level == 0:
                self.state = 0
        else:
            self.ticks_since_last_update = 0


    def tick(self):
        self.image = pygame.image.load(image_state_map[self.state])


class Tile(pygame.sprite.Sprite):
    def __init__(self, x, y):
        pygame.sprite.Sprite.__init__(self)
        self.x = x
        self.y = y
        self.typ = START_MAP[y, x]
        self._next_type = self.typ
        self.water_level = 0 if self.typ in [-1, 0] else 15
        self._water_level_next = self.water_level
        self.item = None

        self._set_type(self.typ)
        self.rect = self.image.get_rect()
        self.rect.update(get_pos(x, y), self.rect.size)

    @property
    def up(self):
        return tile_map[self.y-1][self.x] if self.y else None

    @property
    def down(self):
        return tile_map[self.y+1][self.x] if self.y < len(tile_map) - 1 else None

    @property
    def left(self):
        return tile_map[self.y][self.x-1] if self.x else None

    @property
    def right(self):
        return tile_map[self.y][self.x+1] if self.x < len(tile_map[0]) - 1 else None

    def _max_touching_water(self):
        touching = []
        for dir in [self.up, self.down, self.right, self.left]:
            if dir:
                touching.append(dir.water_level)
        return None if not len(touching) else max(touching)

    def _set_type(self, typ):
        if self.typ == 0:
            self.water_level = 0
        self.typ = typ
        self._next_type = typ
        if self.water_level:
            self.image = pygame.image.load("water.png")
        else:
            self.image = pygame.image.load(image_map[self.typ])

    def update(self):
        if self.typ == -1 or (self.typ > 100 and self.typ < 110):
            max_touching = self._max_touching_water()
            if max_touching:
                self._water_level_next = max_touching - 1
            else:
                self._water_level_next = 0

    def tick(self):
        self.water_level = self._water_level_next
        self._set_type(self._next_type)

    def mouse_left_click(self, pos):
        global money
        if not self.rect.collidepoint(pos):
            return

        if self.water_level and not self.item.state:
            self.item.state = 1
            money -= 5
        elif self.item.state:
            self.item.state = 0
            money += 5

    def mouse_right_click(self, pos):
        if not self.rect.collidepoint(pos):
            return

        if self.typ == -1:
            self._set_type(0)
            self._water_level_next = 0
        elif self.typ == 0:
            self._set_type(-1)


class Engine:
    def __init__(self):
        self.width = 640
        self.height = 480

        pygame.init()
        pygame.font.init()
        self.screen = pygame.display.set_mode((self.width, self.height))

    def run(self):
        global money
        tiles = pygame.sprite.Group()
        items = pygame.sprite.Group()
        for y in range(START_MAP.shape[0]):
            for x in range(START_MAP.shape[1]):
                tile = Tile(x, y)
                tile_map[y][x] = tile
                tiles.add(tile)
                item = Item(tile)
                tile.item = item
                items.add(item)

        character = Character()
        font = pygame.font.SysFont("arial", 20)

        clock = pygame.time.Clock()
        while True:
            clock.tick(16)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:
                        for object in tiles:
                            object.mouse_left_click(event.pos)
                    elif event.button == 3:
                        for object in tiles:
                            object.mouse_right_click(event.pos)
                if event.type == pygame.KEYDOWN:
                    if event.key== pygame.K_w:
                        character.go_up()
                    elif event.key== pygame.K_s:
                        character.go_down()
                    elif event.key== pygame.K_a:
                        character.go_left()
                    elif event.key== pygame.K_d:
                        character.go_right()

            for object in tiles:
                object.update()
            for object in tiles:
                object.tick()
            for object in items:
                object.update()
            for object in items:
                object.tick()
            character.update()
            character.tick()

            text_money_surface = font.render(f"Money: {money}", False, (0, 0, 0))

            self.screen.fill((255, 255, 255))
            tiles.draw(self.screen)
            items.draw(self.screen)
            self.screen.blit(character.image, character.rect)
            self.screen.blit(text_money_surface, (0, 0))
            pygame.display.flip()


if __name__ == '__main__':
    engine = Engine()
    engine.run()
