import pygame
import sys
import random

pygame.init()

# -------------------- Config --------------------
WIDTH, HEIGHT = 600, 400
BLOCK_SIZE = 20
SPEED = 7

SPAWN_INTERVAL_MS = 5000
LIFE_TIME_MS = 5000

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake Game 🐍")
clock = pygame.time.Clock()

# Fonts
font = pygame.font.SysFont("Tahoma", 20)
small_font = pygame.font.SysFont("Tahoma", 16)
big_font = pygame.font.SysFont("Tahoma", 40)

# Colors
HEAD_C = (0, 255, 0)
BODY_C = (0, 200, 0)
TAIL_C = (0, 150, 0)
BG_C = (0, 0, 0)

RED_C   = (255, 0, 0)
YELL_C  = (255, 220, 0)
BROWN_C = (140, 90, 40)


# -------------------- Helpers --------------------
def draw_text(text, color, x, y, center=False, font_obj=None):
    if font_obj is None:
        font_obj = font
    img = font_obj.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    screen.blit(img, rect)


def random_grid_pos(occupied):
    while True:
        x = random.randrange(0, WIDTH, BLOCK_SIZE)
        y = random.randrange(0, HEIGHT, BLOCK_SIZE)
        if (x, y) not in occupied:
            return (x, y)


# -------------------- UI Screens --------------------
def start_screen():
    button_rect = pygame.Rect((WIDTH - 220)//2, HEIGHT - 95, 220, 60)

    rules = [
        "Apple Rules:",
        "Red: +1 score, +1 length (always)",
        "Yellow: +3 score, +3 length",
        "  Appears every 5s, lasts 5s",
        "Brown: -3 score, -3 length",
        "  Appears every 5s, lasts 5s",
        "",
        "Controls: Arrows or WASD",
        "ESC = Pause | Q = Quit",
    ]

    while True:
        screen.fill((20, 20, 20))
        draw_text("Snake Game", (0, 255, 0), WIDTH//2, 45, True, big_font)

        pygame.draw.rect(screen, (50, 150, 50), button_rect, border_radius=10)
        draw_text("START", (255, 255, 255),
                  WIDTH//2, button_rect.centery, True, big_font)

        y = 95
        for line in rules:
            draw_text(line, (220, 220, 220), 30, y, False, small_font)
            y += 18

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return
            if event.type == pygame.MOUSEBUTTONDOWN and button_rect.collidepoint(event.pos):
                return


def pause_screen():
    while True:
        screen.fill(BG_C)
        draw_text("PAUSED", (255, 255, 0), WIDTH//2, HEIGHT//2 - 20, True, big_font)
        draw_text("Press ESC or P to continue", (200, 200, 200),
                  WIDTH//2, HEIGHT//2 + 20, True, font)
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_p):
                return


def game_over_screen(score):
    while True:
        screen.fill(BG_C)
        draw_text("GAME OVER", (255, 255, 255), WIDTH//2, HEIGHT//2 - 40, True, big_font)
        draw_text(f"Score: {score}", (255, 255, 255), WIDTH//2, HEIGHT//2, True, font)
        draw_text("R = Restart | Q = Quit", (200, 200, 200),
                  WIDTH//2, HEIGHT//2 + 40, True, font)
        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_r:
                    return "restart"
                if e.key == pygame.K_q:
                    pygame.quit(); sys.exit()


# -------------------- Core Classes --------------------
class Snake:
    def __init__(self):
        x, y = WIDTH//2, HEIGHT//2
        self.body = [(x, y), (x - BLOCK_SIZE, y)]
        self.dx, self.dy = BLOCK_SIZE, 0
        self.grow = 0

    def set_direction(self, dx, dy):
        if (dx, dy) != (-self.dx, -self.dy):
            self.dx, self.dy = dx, dy

    def next_head(self):
        x, y = self.body[0]
        return ((x + self.dx) % WIDTH, (y + self.dy) % HEIGHT)

    def move(self):
        self.body.insert(0, self.next_head())
        if self.grow > 0:
            self.grow -= 1
        else:
            self.body.pop()

    def add_length(self, n): self.grow += n
    def remove_length(self, n):
        while len(self.body) > 2 and n > 0:
            self.body.pop(); n -= 1

    def draw(self):
        for i, (x, y) in enumerate(self.body):
            c = HEAD_C if i == 0 else TAIL_C if i == len(self.body)-1 else BODY_C
            pygame.draw.rect(screen, c, (x, y, BLOCK_SIZE, BLOCK_SIZE))


class Food:
    def __init__(self, color, points, always=False, respawn=None, lifetime=None):
        self.color = color
        self.points = points
        self.always = always
        self.respawn = respawn
        self.lifetime = lifetime
        self.pos = None
        self.spawn_time = 0
        self.next_spawn = 0

    def spawn(self, now, occupied):
        if self.pos is None and now >= self.next_spawn:
            self.pos = random_grid_pos(occupied)
            self.spawn_time = now

    def update(self, now):
        if self.pos and self.lifetime and now - self.spawn_time >= self.lifetime:
            self.despawn(now)

    def despawn(self, now):
        self.pos = None
        self.next_spawn = now if self.always else now + self.respawn

    def draw(self):
        if self.pos:
            pygame.draw.rect(screen, self.color, (*self.pos, BLOCK_SIZE, BLOCK_SIZE))


class Game:
    def __init__(self):
        self.reset()

    def reset(self):
        self.snake = Snake()
        self.score = 0
        self.first_red_eaten = False
        now = pygame.time.get_ticks()

        self.red = Food(RED_C, 1, always=True)
        self.yellow = Food(YELL_C, 3, respawn=SPAWN_INTERVAL_MS, lifetime=LIFE_TIME_MS)
        self.brown = Food(BROWN_C, -3, respawn=SPAWN_INTERVAL_MS, lifetime=LIFE_TIME_MS)

        self.red.next_spawn = now
        self.yellow.next_spawn = 10**15
        self.brown.next_spawn = 10**15

    def foods(self):
        return [self.red] if not self.first_red_eaten else [self.red, self.yellow, self.brown]

    def update(self):
        now = pygame.time.get_ticks()
        occupied = set(self.snake.body)

        for f in self.foods():
            f.spawn(now, occupied)
            if f.pos:
                occupied.add(f.pos)

        for f in self.foods():
            f.update(now)

        nh = self.snake.next_head()
        if nh in self.snake.body:
            return "game_over"

        eaten = None
        for f in self.foods():
            if f.pos == nh:
                eaten = f

        self.snake.move()

        if eaten:
            self.score += eaten.points
            if eaten.points > 0:
                self.snake.add_length(eaten.points)
            else:
                self.snake.remove_length(-eaten.points)

            eaten.despawn(now)

            if eaten is self.red and not self.first_red_eaten:
                self.first_red_eaten = True
                self.yellow.next_spawn = now + SPAWN_INTERVAL_MS
                self.brown.next_spawn = now + SPAWN_INTERVAL_MS

        return "ok"

    def render(self):
        screen.fill(BG_C)
        self.snake.draw()
        for f in self.foods():
            f.draw()
        draw_text(f"Score: {self.score}", (255, 255, 255), 10, 10)
        pygame.display.flip()

    def run(self):
        start_screen()
        while True:
            clock.tick(SPEED)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        pause_screen()
                    if e.key in (pygame.K_UP, pygame.K_w):
                        self.snake.set_direction(0, -BLOCK_SIZE)
                    if e.key in (pygame.K_DOWN, pygame.K_s):
                        self.snake.set_direction(0, BLOCK_SIZE)
                    if e.key in (pygame.K_LEFT, pygame.K_a):
                        self.snake.set_direction(-BLOCK_SIZE, 0)
                    if e.key in (pygame.K_RIGHT, pygame.K_d):
                        self.snake.set_direction(BLOCK_SIZE, 0)

            if self.update() == "game_over":
                if game_over_screen(self.score) == "restart":
                    self.reset()
                    start_screen()

            self.render()


if __name__ == "__main__":
    Game().run()
