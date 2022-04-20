import pygame as pg
import random
import numpy as np

# parameter
MAX_PELLET = 64
MAX_LANDMINES = 8
MAX_POWER = 4
Weight = 520
Height = 401
PAC_MAN = "../pic/pacman/"
GHOST = "../pic/ghost/"
BLACK = (0, 0, 0)
SKYBLUE = (0, 191, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
GREEN_YELLOW = (54, 255, 165)
BOMB_COLOR = (241, 91, 108)
# 401*401,16*16
wall_positions = [
    # border
    [0, 0, 401, 1],
    [0, 0, 1, 401],
    [400, 0, 1, 401],
    [0, 400, 401, 1],
    # wall
    [25, 25, 200, 1],
    [275, 25, 25, 1],
    [125, 50, 100, 1],
    [100, 75, 50, 1],
    [200, 75, 75, 1],
    [350, 75, 50, 1],
    [150, 100, 75, 1],
    [0, 125, 50, 1],
    [100, 125, 75, 1],
    [325, 125, 50, 1],
    [150, 150, 25, 1],
    [275, 150, 75, 1],
    [50, 175, 25, 1],
    [250, 175, 75, 1],
    [25, 200, 125, 1],
    [375, 200, 25, 1],
    [50, 225, 25, 1],
    [125, 225, 25, 1],
    [275, 225, 75, 1],
    [25, 250, 50, 1],
    [150, 250, 200, 1],
    [75, 275, 100, 1],
    [225, 275, 50, 1],
    [300, 275, 75, 1],
    [0, 300, 200, 1],
    [250, 300, 75, 1],
    [25, 325, 100, 1],
    [0, 350, 25, 1],
    [50, 350, 75, 1],
    [175, 350, 200, 1],
    [25, 375, 50, 1],
    [100, 375, 100, 1],
    [275, 375, 50, 1],
    [350, 375, 25, 1],
    [25, 50, 1, 50],
    [25, 150, 1, 75],
    [50, 25, 1, 75],
    [50, 125, 1, 25],
    [50, 250, 1, 50],
    [75, 50, 1, 100],
    [100, 25, 1, 50],
    [100, 100, 1, 75],
    [100, 200, 1, 75],
    [125, 150, 1, 50],
    [125, 225, 1, 25],
    [150, 150, 1, 25],
    [150, 300, 1, 75],
    [175, 50, 1, 50],
    [175, 225, 1, 25],
    [175, 325, 1, 25],
    [200, 125, 1, 50],
    [200, 275, 1, 50],
    [225, 100, 1, 50],
    [225, 275, 1, 50],
    [225, 375, 1, 25],
    [250, 25, 1, 50],
    [250, 100, 1, 50],
    [250, 175, 1, 50],
    [250, 325, 1, 50],
    [275, 100, 1, 50],
    [275, 300, 1, 25],
    [300, 25, 1, 100],
    [300, 200, 1, 25],
    [300, 325, 1, 25],
    [325, 0, 1, 100],
    [325, 175, 1, 25],
    [325, 300, 1, 25],
    [350, 25, 1, 50],
    [350, 100, 1, 25],
    [350, 175, 1, 50],
    [350, 300, 1, 50],
    [375, 25, 1, 25],
    [375, 125, 1, 50],
    [375, 225, 1, 100],
]


# for wall
class Wall(pg.sprite.Sprite):
    def __init__(self, x, y, width, height, color, **kwargs):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.left = x
        self.rect.top = y


# for food
class Food(pg.sprite.Sprite):
    def __init__(self, x, y, width, height, color, bg_color, **kwargs):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.Surface([width, height])
        self.image.fill(bg_color)
        self.image.set_colorkey(bg_color)
        pg.draw.ellipse(self.image, color, [0, 0, width, height])
        self.rect = self.image.get_rect()
        self.rect.left = x
        self.rect.top = y

# for save block
class Block(pg.sprite.Sprite):
    def __init__(self, x, y, width, height, bg_color, **kwargs):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.Surface([width, height])
        self.image.fill(bg_color)
        self.rect = self.image.get_rect()
        self.rect.left = x
        self.rect.top = y


# for character
class Player(pg.sprite.Sprite):
    def __init__(self, x, y, role_image_path):
        pg.sprite.Sprite.__init__(self)
        self.role_name = role_image_path.split('/')[-1].split('.')[0]
        self.base_image = pg.transform.scale(pg.image.load(role_image_path).convert(), (69, 23))
        self.animation_image = self.base_image.subsurface(pg.Rect(0, 0, 23, 23))
        self.image = self.animation_image.copy()
        self.rect = self.image.get_rect()
        self.rect.left = x
        self.rect.top = y
        self.prev_x = x
        self.prev_y = y
        self.base_speed = [5, 5]
        self.speed = [0, 0]
        self.is_move = False
        # this is for super power
        self.super = False
        self.super_time = 0
        self.score = 0
        self.landmine = 0
        self.animation_tick = 0
        self.animation_type = 0
        # this is for super after setting landmine
        self.superman_time = 0
        self.clock = None
        self.dead_time = 0

    # change direction
    def changedirection(self, direction, wall_sprites):
        if self.super:
            # make player at the center of block
            if (self.rect.top - 1) % 25 == 1: self.rect.top -= 1
            if (self.rect.top - 1) % 25 == 24: self.rect.top += 1
            if (self.rect.left - 1) % 25 == 1: self.rect.left -= 1
            if (self.rect.left - 1) % 25 == 24: self.rect.left += 1
        if (self.rect.top - 2) % 25 == 2: self.rect.top -= 2
        if (self.rect.top - 2) % 25 == 23: self.rect.top += 2
        if (self.rect.left - 2) % 25 == 2: self.rect.left -= 2
        if (self.rect.left - 2) % 25 == 23: self.rect.left += 2
        # left
        if direction[0] < 0:
            if (self.rect.top - 1) % 25 != 0 or self.speed[0] > 0: return False
        # right
        elif direction[0] > 0:
            if (self.rect.top - 1) % 25 != 0 or self.speed[0] < 0: return False
        # up
        elif direction[1] < 0:
            if (self.rect.left - 1) % 25 != 0 or self.speed[1] > 0: return False
        # down
        elif direction[1] > 0:
            if (self.rect.left - 1) % 25 != 0 or self.speed[1] < 0: return False
        # collision: for enable turn left/right or not
        x_prev = self.rect.left
        y_prev = self.rect.top
        self.rect.left += direction[0] * self.base_speed[0]
        self.rect.top += direction[1] * self.base_speed[1]
        is_collision = pg.sprite.spritecollide(self, wall_sprites, False)
        self.rect.left = x_prev
        self.rect.top = y_prev
        if is_collision:
            return False
        # update speed by current direction
        self.speed = [direction[0] * self.base_speed[0], direction[1] * self.base_speed[1]]
        return self.speed

    # update position
    def update(self, wall_sprites):
        if self.dead_time > 0 :
            self.dead_time -= 1
        if self.superman_time > 0:
            self.superman_time -= 1
        if not self.is_move or self.dead_time > 0:
            return False
        # get next expected position
        self.rect.left += self.speed[0]
        self.rect.top += self.speed[1]
        is_collide = pg.sprite.spritecollide(self, wall_sprites, False)

        shift = False
        if is_collide:
            if self.speed[0] > 0 or self.speed[1] > 0:
                shift = True
            while True:
                # make player stick on wall
                self.rect.left -= self.speed[0] / self.base_speed[0]
                self.rect.top -= self.speed[1] / self.base_speed[1]
                is_collide = pg.sprite.spritecollide(self, wall_sprites, False)
                if not is_collide:
                    if shift:
                        self.rect.left -= self.speed[0] / self.base_speed[0]
                        self.rect.top -= self.speed[1] / self.base_speed[1]
                    break
        # animation's direction control
        self.animation_tick += 1
        if self.animation_tick % 3 == 0:
            self.animation_tick = 0
            self.animation_type += 1
            if self.animation_type > 2: self.animation_type = 0
            self.animation_image = self.base_image.subsurface(pg.Rect(self.animation_type * 23, 0, 23, 23))
            if self.speed[0] < 0:
                self.image = pg.transform.flip(self.animation_image, True, False)
            elif self.speed[0] > 0:
                self.image = self.animation_image.copy()
            elif self.speed[1] < 0:
                self.image = pg.transform.rotate(self.animation_image, 90)
            elif self.speed[1] > 0:
                self.image = pg.transform.rotate(self.animation_image, -90)
        return True

    # if dead, reset position
    def movePosition(self):
        x = random.choice([176, 201])
        y = random.choice([176, 201])
        self.rect.left = x
        self.rect.top = y
        self.prev_x = x
        self.prev_y = y
        self.is_move = False


class Ghost(pg.sprite.Sprite):
    def __init__(self, x, y, role_image_path):
        pg.sprite.Sprite.__init__(self)
        self.role_name = role_image_path.split('/')[-1].split('.')[0]
        self.base_image = pg.transform.scale(pg.image.load(role_image_path).convert(), (92, 23))
        self.animation_image = self.base_image.subsurface(pg.Rect(0, 0, 23, 23))
        self.image = self.animation_image.copy()
        self.rect = self.image.get_rect()
        self.rect.left = x
        self.rect.top = y
        self.prev_x = x
        self.prev_y = y
        self.base_speed = [5, 5]
        self.is_move = True
        self.super = False
        self.speed = self.randomDirection()
        self.dead_time = 0

    # update position
    def update(self, wall_sprites):
        if self.dead_time > 0:
            self.dead_time -= 1
        if not self.is_move or self.dead_time > 0:
            return False
        # ramdom move for ghost
        if (self.rect.top - 1) % 25 == 0 and (self.rect.left - 1) % 25 == 0:
            base_direction = [[-5, 0], [5, 0], [0, 5], [0, -5]]
            if self.speed[0] < 0:
                base_direction.remove([5, 0])
            elif self.speed[0] > 0:
                base_direction.remove([-5, 0])
            elif self.speed[1] < 0:
                base_direction.remove([0, 5])
            elif self.speed[1] > 0:
                base_direction.remove([0, -5])

            avail_direction = []
            for direction in base_direction:
                x_prev, y_prev = self.rect.left, self.rect.top
                self.rect.left += direction[0]
                self.rect.top += direction[1]
                is_collide = pg.sprite.spritecollide(self, wall_sprites, False)
                self.rect.left, self.rect.top = x_prev, y_prev
                if is_collide:
                    continue
                avail_direction.append(direction)
            self.speed = random.choice(avail_direction)
        x_prev = self.rect.left
        y_prev = self.rect.top
        self.rect.left += self.speed[0]
        self.rect.top += self.speed[1]
        is_collide = pg.sprite.spritecollide(self, wall_sprites, False)
        if is_collide:
            self.rect.left = x_prev
            self.rect.top = y_prev
            return False

        if self.speed[0] > 0:
            self.image = pg.transform.flip(self.animation_image, True, False)
        elif self.speed[0] < 0:
            self.image = self.animation_image.copy()
        elif self.speed[1] < 0:
            self.image = pg.transform.rotate(self.animation_image, -90)
        elif self.speed[1] > 0:
            self.image = pg.transform.rotate(self.animation_image, 90)
        return True

    # random direction
    def randomDirection(self):
        return random.choice([[-5, 0], [5, 0], [0, 5], [0, -5]])

    def movePosition(self):
        x = random.choice([176, 201])
        y = random.choice([176, 201])
        self.rect.left = x
        self.rect.top = y
        self.prev_x = x
        self.prev_y = y


# map 1
class Game(object):
    # init parameter
    def __init__(self, walls=wall_positions):
        self.info = "map1"
        self.Pellet_num = 0
        self.Landmines_num = 0
        self.Power_num = 0
        self.Wall = walls

    # set wall
    def setupWalls(self, wall_color):
        self.wall_sprites = pg.sprite.Group()
        self.safe_place = pg.sprite.Group()
        self.safe_place.add(Block(175, 175, 50, 50, GREEN_YELLOW))

        for wall_position in self.Wall:
            wall = Wall(*wall_position, wall_color)
            self.wall_sprites.add(wall)
        return self.wall_sprites, self.safe_place

    # set player
    def setPlayer(self, hero_image_path):
        self.hero_sprites = pg.sprite.Group()
        self.hero_sprites.add(Player(176, 176, hero_image_path+"pacman_yellow.png"))
        self.hero_sprites.add(Player(201, 176, hero_image_path+"pacman_pink.png"))
        self.hero_sprites.add(Player(176, 201, hero_image_path+"pacman_orange.png"))
        self.hero_sprites.add(Player(201, 201, hero_image_path+"pacman_purple.png"))
        return self.hero_sprites

    # set ghost
    def setGhost(self, ghost_image_path):
        self.ghost_sprites = pg.sprite.Group()
        self.ghost_sprites.add(Ghost(176, 176, ghost_image_path + 'blueGhost.png'))
        self.ghost_sprites.add(Ghost(201, 176, ghost_image_path + "blueGhost.png"))
        self.ghost_sprites.add(Ghost(176, 201, ghost_image_path + "blueGhost.png"))
        self.ghost_sprites.add(Ghost(201, 201, ghost_image_path + "blueGhost.png"))
        return self.ghost_sprites

    # set pellet
    def setPellet(self, color, bg_color):
        self.Pellet_sprites = pg.sprite.Group()
        prob = MAX_PELLET / (16 ** 2)
        for row in range(16):
            for col in range(16):
                if (row == 7 or row == 8) and (col == 7 or col == 8):
                    continue
                if random.random() < prob and self.Pellet_num < MAX_PELLET:
                    pellet = Food(25 * row + 11, 25 * col + 11, 5, 5, color, bg_color)
                    is_collide_l = pg.sprite.spritecollide(pellet, self.Landmines_sprites, False)
                    is_collide_p = pg.sprite.spritecollide(pellet, self.Power_sprites, False)
                    if is_collide_l or is_collide_p: continue
                    self.Pellet_sprites.add(pellet)
                    self.Pellet_num += 1

        return self.Pellet_sprites

    # set landmine
    def setLandmines(self, color, bg_color):
        self.Landmines_sprites = pg.sprite.Group()
        prob = MAX_LANDMINES / (16 ** 2)
        for row in range(16):
            for col in range(16):
                if (row == 7 or row == 8) and (col == 7 or col == 8):
                    continue
                if random.random() < prob and self.Landmines_num < MAX_LANDMINES:
                    landmine = Food(25 * row + 8, 25 * col + 8, 11, 11, color, bg_color)
                    self.Landmines_sprites.add(landmine)
                    self.Landmines_num += 1
        return self.Landmines_sprites

    # set power
    def setPower(self, color, bg_color):
        self.Power_sprites = pg.sprite.Group()
        prob = MAX_POWER / (16 ** 2)
        for row in range(16):
            for col in range(16):
                if (row == 7 or row == 8) and (col == 7 or col == 8):
                    continue
                if random.random() < prob and self.Power_num < MAX_POWER:
                    Power = Food(25 * row + 8, 25 * col + 8, 11, 11, color, bg_color)
                    is_collide = pg.sprite.spritecollide(Power, self.Landmines_sprites, False)
                    if is_collide: continue
                    self.Power_sprites.add(Power)
                    self.Power_num += 1
        return self.Power_sprites

    # set bomb
    def setBomb(self):
        self.Bomb_sprites = pg.sprite.Group()
        return self.Bomb_sprites

# random create map
def createMap():
    parallel_wall = np.random.rand(16, 17)
    vertical_wall = np.random.rand(17, 16)
    p_wall = parallel_wall < 0.3
    v_wall = vertical_wall < 0.3

    # border
    for i in range(16):
        p_wall[i][0] = 1
        p_wall[i][16] = 1
    v_wall[0] = np.ones(16)
    v_wall[16] = np.ones(16)

    # corner
    p_wall[0][1] = 0
    p_wall[0][15] = 0
    p_wall[15][1] = 0
    p_wall[15][15] = 0
    v_wall[1][0] = 0
    v_wall[1][15] = 0
    v_wall[15][0] = 0
    v_wall[15][15] = 0

    # center
    p_wall[7][8] = 0
    p_wall[8][8] = 0
    p_wall[7][7] = 0
    p_wall[8][7] = 0
    p_wall[7][9] = 0
    p_wall[8][9] = 0

    v_wall[8][7] = 0
    v_wall[8][8] = 0
    v_wall[7][7] = 0
    v_wall[7][8] = 0
    v_wall[9][7] = 0
    v_wall[9][8] = 0

    n_walls = np.zeros([16, 16])
    # detect for blind alley
    for i in range(16):
        for j in range(16):
            walls = []
            # up
            if p_wall[i][j]:
                walls.append("up")
                n_walls[i][j] += 1
            # bottom
            if p_wall[i][j + 1]:
                walls.append("bottom")
                n_walls[i][j] += 1
            # left
            if v_wall[i][j]:
                walls.append("left")
                n_walls[i][j] += 1
            # right
            if v_wall[i + 1][j]:
                walls.append("right")
                n_walls[i][j] += 1

            # print(f"{i}x{j}={n_walls[i][j]}, {walls}")

            # surrounded by wall
            if len(walls) > 2:
                n_remove = len(walls) - 2
                # avoid to remove map border
                if i == 0:
                    if "left" in walls: walls.remove("left")
                elif i == 15:
                    if "right" in walls: walls.remove("right")
                if j == 0:
                    if "up" in walls: walls.remove("up")
                elif j == 15:
                    if "bottom" in walls: walls.remove("bottom")
                # print(f"{i}x{j} remove {n_remove}, {walls}")
                # remove wall
                for t in range(n_remove):
                    temp = np.random.choice(walls)
                    walls.remove(temp)
                    # print(f"{i}x{j} remove {temp}")
                    if temp == "left":
                        v_wall[i][j] = 0
                        n_walls[i][j] -= 1
                    elif temp == "right":
                        v_wall[i + 1][j] = 0
                        n_walls[i][j] -= 1
                    elif temp == "up":
                        p_wall[i][j] = 0
                        n_walls[i][j] -= 1
                    elif temp == "bottom":
                        p_wall[i][j + 1] = 0
                        n_walls[i][j] -= 1
    # print(n_walls)

    return p_wall, v_wall

def drawWall(p_wall, v_wall):
    wall_UI_pos = []
    for i in range(16):
        for j in range(17):
            if p_wall[i][j]:
                x = i * 25
                y = j * 25
                wall_UI_pos.append([x, y, 25, 1])
    for i in range(17):
        for j in range(16):
            if v_wall[i][j]:
                x = i * 25
                y = j * 25
                wall_UI_pos.append([x, y, 1, 25])
    return wall_UI_pos


def text_to_screen(screen, text, x, y, size=50, color=(255, 255, 255), font_type=None):
    try:
        text = str(text)
        # font = pg.font.Font(font_type, size)
        font = pg.font.SysFont(None, 24)
        text = font.render(text, True, color)
        screen.blit(text, (x, y))
    except Exception as e:
        print('Font Error, saw it coming')
        raise e


def initialize():
    pg.init()
    screen = pg.display.set_mode([Weight, Height])
    pg.display.set_caption('Pacman')
    return screen


if __name__ == "__main__":
    """main()"""
    screen = initialize()

    pW, vW = createMap()
    wall_positions = drawWall(pW, vW)
    level = Game(wall_positions)
