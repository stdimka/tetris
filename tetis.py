import pygame
import random
import os

# Константы
SCREEN_WIDTH, SCREEN_HEIGHT = 300, 600
BLOCK_SIZE = 30
COLS, ROWS = SCREEN_WIDTH // BLOCK_SIZE, SCREEN_HEIGHT // BLOCK_SIZE
BLACK, GRAY, WHITE = (0, 0, 0), (128, 128, 128), (255, 255, 255)

# Инициализация Pygame
pygame.init()

# Настройки текстур
TEXTURE_FOLDER = "textures"
if not os.path.exists(TEXTURE_FOLDER):
    os.makedirs(TEXTURE_FOLDER)
TEXTURE_FILES = [f for f in os.listdir(TEXTURE_FOLDER) if f.endswith(".png")]

def load_random_texture():
    """ Загружает случайную текстуру по требованию. """
    if not TEXTURE_FILES:
        return pygame.Surface((BLOCK_SIZE, BLOCK_SIZE))
    texture_file = random.choice(TEXTURE_FILES)
    return pygame.transform.scale(
        pygame.image.load(os.path.join(TEXTURE_FOLDER, texture_file)),
        (BLOCK_SIZE, BLOCK_SIZE)
    )

# Фигуры
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1, 1], [0, 1, 0]],  # T
    [[1, 1], [1, 1]],  # O
    [[1, 1, 0], [0, 1, 1]],  # S
    [[0, 1, 1], [1, 1, 0]],  # Z
    [[1, 1, 1], [1, 0, 0]],  # L
    [[1, 1, 1], [0, 0, 1]]  # J
]

class Tetromino:
    def __init__(self, x, y):
        self.shape = random.choice(SHAPES)
        self.textures = [[load_random_texture() if cell else None for cell in row] for row in self.shape]
        self.x, self.y = x, y

    def rotate(self):
        self.shape = [list(row) for row in zip(*self.shape[::-1])]
        self.textures = [list(row) for row in zip(*self.textures[::-1])]

class Tetris:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Tetris with Dynamic Textures")
        self.clock = pygame.time.Clock()
        self.grid = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.current_piece = Tetromino(COLS // 2, 0)
        self.running, self.game_over = True, False
        self.fall_time, self.fall_speed = 0, 500
        self.score = 0  # Добавляем счётчик очков

    def check_collision(self, dx=0, dy=0, rotated=False):
        shape = self.current_piece.shape
        if rotated:
            shape = [list(row) for row in zip(*shape[::-1])]
        for y, row in enumerate(shape):
            for x, cell in enumerate(row):
                if cell:
                    nx = self.current_piece.x + x + dx
                    ny = self.current_piece.y + y + dy
                    if nx < 0 or nx >= COLS or ny < 0 or ny >= ROWS:
                        return True
                    if ny >= 0 and self.grid[ny][nx] is not None:
                        return True
        return False

    def merge_piece(self):
        for y, row in enumerate(self.current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.grid[self.current_piece.y + y][self.current_piece.x + x] = self.current_piece.textures[y][x]

    def clear_lines(self):
        new_grid = [row for row in self.grid if None in row]
        cleared = len(self.grid) - len(new_grid)
        self.grid = [[None] * COLS for _ in range(cleared)] + new_grid
        # Начисляем очки за очищенные линии
        if cleared > 0:
            self.score += cleared * 100  # 100 очков за каждую очищенную линию

    def spawn_piece(self):
        self.current_piece = Tetromino(COLS // 2, 0)
        if self.check_collision():
            self.game_over = True

    def move(self, dx, dy):
        if not self.check_collision(dx=dx, dy=dy):
            self.current_piece.x += dx
            self.current_piece.y += dy

    def rotate_piece(self):
        if not self.check_collision(rotated=True):
            self.current_piece.rotate()

    def drop_piece(self):
        while not self.check_collision(dy=1):
            self.current_piece.y += 1

    def update(self):
        self.fall_time += self.clock.get_time()
        if self.fall_time >= self.fall_speed:
            self.fall_time = 0
            if self.check_collision(dy=1):
                self.merge_piece()
                self.clear_lines()
                self.spawn_piece()
            else:
                self.current_piece.y += 1

    def draw_grid(self):
        for y in range(ROWS):
            for x in range(COLS):
                cell = self.grid[y][x]
                if cell is not None:
                    self.screen.blit(cell, (x * BLOCK_SIZE, y * BLOCK_SIZE))
                pygame.draw.rect(self.screen, GRAY,
                                (x * BLOCK_SIZE, y * BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

    def draw_piece(self):
        for y, row in enumerate(self.current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    texture = self.current_piece.textures[y][x]
                    if texture:
                        self.screen.blit(texture,
                                        ((self.current_piece.x + x) * BLOCK_SIZE,
                                         (self.current_piece.y + y) * BLOCK_SIZE))

    def draw_score(self):
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))  # Отображаем счёт в верхнем левом углу

    def run(self):
        while self.running:
            self.screen.fill(BLACK)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.move(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        self.move(1, 0)
                    elif event.key == pygame.K_DOWN:
                        self.move(0, 1)
                    elif event.key == pygame.K_UP:
                        self.rotate_piece()
                    elif event.key == pygame.K_SPACE:
                        self.drop_piece()

            if not self.game_over:
                self.update()
                self.draw_grid()
                self.draw_piece()
                self.draw_score()  # Отображаем счёт
            else:
                font = pygame.font.Font(None, 36)
                text = font.render("Game Over", True, WHITE)
                self.screen.blit(text, (SCREEN_WIDTH//4, SCREEN_HEIGHT//2))

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    game = Tetris()
    game.run()