import pygame
import random
import os
import json

# Константы
SCREEN_WIDTH, SCREEN_HEIGHT = 300, 600
BLOCK_SIZE = 30
COLS, ROWS = SCREEN_WIDTH // BLOCK_SIZE, SCREEN_HEIGHT // BLOCK_SIZE
BLACK = (25, 25, 25)
WHITE = (245, 245, 245)
GRAY = (130, 130, 130)

# Цвета в стиле делового кежуал
CASUAL_COLORS = [
    (202, 192, 179, 180),  # I - Beige
    (74, 78, 77, 180),  # T - Charcoal
    (150, 137, 115, 180),  # O - Sage
    (84, 93, 85, 180),  # S - Olive
    (129, 96, 82, 180),  # Z - Terracotta
    (82, 102, 114, 180),  # L - Steel Blue
    (120, 105, 86, 180)  # J - Khaki
]

# Настройки текстур
TEXTURE_FOLDER = "textures"
if not os.path.exists(TEXTURE_FOLDER):
    os.makedirs(TEXTURE_FOLDER)
TEXTURE_FILES = [f for f in os.listdir(TEXTURE_FOLDER) if f.endswith(".png")]

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


class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.radius = random.randint(2, 5)
        self.speed_x = random.uniform(-1, 1)
        self.speed_y = random.uniform(-2, 0)
        self.life = 30

    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.life -= 1
        self.radius = max(1, self.radius - 0.1)

    def draw(self, screen):
        if self.life > 0:
            pygame.draw.circle(screen, self.color,
                               (int(self.x), int(self.y)), int(self.radius))


class Tetromino:
    def __init__(self, x, y):
        shape_idx = random.randint(0, len(SHAPES) - 1)
        self.shape = SHAPES[shape_idx]
        self.color = CASUAL_COLORS[shape_idx]
        self.textures = [[self.load_texture() if cell else None for cell in row] for row in self.shape]
        self.x, self.y = x, y

    def load_texture(self):
        if TEXTURE_FILES:
            texture_file = random.choice(TEXTURE_FILES)
            return pygame.transform.scale(
                pygame.image.load(os.path.join(TEXTURE_FOLDER, texture_file)),
                (BLOCK_SIZE, BLOCK_SIZE)
            )
        return pygame.Surface((BLOCK_SIZE, BLOCK_SIZE))

    def rotate(self):
        new_shape = [list(row) for row in zip(*self.shape[::-1])]
        new_textures = [list(row) for row in zip(*self.textures[::-1])]
        return new_shape, new_textures


class Tetris:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Business Casual Tetris")

        # Состояния
        self.show_menu = True
        self.show_high_scores = False
        self.paused = False
        self.game_over = False

        # Ассеты
        self.load_assets()
        self.reset_game()
        self.particles = []
        self.clock = pygame.time.Clock()
        self.last_fall = pygame.time.get_ticks()

    def load_assets(self):
        # Фон
        try:
            self.background = pygame.image.load("background.png")
            self.background = pygame.transform.scale(self.background, (SCREEN_WIDTH, SCREEN_HEIGHT))
        except:
            self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            self.background.fill(BLACK)


        # Загрузка звуковых эффектов
        self.sounds = {
            'Move': pygame.mixer.Sound('sounds/Move.wav'),
            'Rotate': pygame.mixer.Sound('sounds/Rotate.wav'),
            'Clear': pygame.mixer.Sound('sounds/Clear.wav'),
            'Game over': pygame.mixer.Sound('sounds/Game over.wav')
            # Фоновая музыка удалена по требованию
        }

    def reset_game(self):
        self.grid = [[(None, None) for _ in range(COLS)] for _ in range(ROWS)]
        self.current_piece = Tetromino(COLS // 2 - 2, 0)
        self.next_piece = Tetromino(COLS // 2 - 2, 0)
        self.score = 0
        self.level = 1
        self.fall_speed = 500
        self.start_time = pygame.time.get_ticks()  # Сброс таймера
        self.game_over = False  # Добавлено явное сброса флага

    def check_collision(self, shape, x, y):
        for cy, row in enumerate(shape):
            for cx, cell in enumerate(row):
                if cell:
                    nx = x + cx
                    ny = y + cy
                    if nx < 0 or nx >= COLS or ny >= ROWS:
                        return True
                    if ny >= 0 and self.grid[ny][nx][0] is not None:
                        return True
        return False

    def merge_piece(self):
        for y, row in enumerate(self.current_piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    self.grid[self.current_piece.y + y][self.current_piece.x + x] = (
                        self.current_piece.textures[y][x],
                        self.current_piece.color
                    )
        lines_cleared = self.clear_lines()
        if lines_cleared > 0:
            self.sounds['Clear'].play()
            self.spawn_particles(lines_cleared)
        self.current_piece = self.next_piece
        self.next_piece = Tetromino(COLS // 2 - 2, 0)
        if self.check_collision(self.current_piece.shape, self.current_piece.x, self.current_piece.y):
            self.game_over = True
            self.sounds['Game over'].play()
            self.save_score()

    def clear_lines(self):
        new_grid = []
        cleared = 0
        for row in self.grid:
            if any(cell[0] is None for cell in row):
                new_grid.append(row)
            else:
                cleared += 1
        # Создаем пустые строки вместо очищенных
        self.grid = [[(None, None)] * COLS for _ in range(cleared)] + new_grid
        # Начисляем очки
        self.score += cleared * 100 * self.level
        # Повышаем уровень каждые 5000 очков
        if cleared > 0 and self.score // 5000 > (self.score - cleared * 100 * self.level) // 5000:
            self.level += 1
            self.fall_speed = max(100, self.fall_speed - 50)
        return cleared

    def spawn_particles(self, lines):
        for _ in range(lines * 20):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT // 2)
            color = random.choice(CASUAL_COLORS)[:3]  # Убираем альфа-канал для частиц
            self.particles.append(Particle(x, y, color))

    def draw_block(self, x, y, texture, color):
        block = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
        pygame.draw.rect(block, color,
                         (0, 0, BLOCK_SIZE, BLOCK_SIZE),
                         border_radius=BLOCK_SIZE // 5)
        if texture:
            block.blit(texture, (0, 0))
        self.screen.blit(block, (x * BLOCK_SIZE, y * BLOCK_SIZE))

    def draw_grid(self):
        for y in range(ROWS):
            for x in range(COLS):
                texture, color = self.grid[y][x]
                if color is not None:
                    self.draw_block(x, y, texture, color)

    def draw_piece(self, piece, offset_x=0, offset_y=0):
        for y, row in enumerate(piece.shape):
            for x, cell in enumerate(row):
                if cell:
                    texture = piece.textures[y][x]
                    color = piece.color
                    self.draw_block(piece.x + x + offset_x,
                                    piece.y + y + offset_y,
                                    texture, color)

    def draw_hud(self):
        font = pygame.font.Font(None, 30)
        score = font.render(f"Score: {self.score}", True, WHITE)
        level = font.render(f"Level: {self.level}", True, WHITE)
        time = font.render(f"Time: {self.get_play_time() // 1000}s", True, WHITE)
        self.screen.blit(score, (10, 10))
        self.screen.blit(level, (10, 40))
        self.screen.blit(time, (10, 70))
        self.draw_piece(self.next_piece, offset_x=COLS + 2, offset_y=2)

    def draw_menu(self):
        self.screen.blit(self.background, (0, 0))
        font = pygame.font.Font(None, 48)
        title = font.render("Business Tetris", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        menu_items = ["Enter - Start", "H - High Scores", "Q - Quit"]
        y_pos = 250
        for item in menu_items:
            text = pygame.font.Font(None, 24).render(item, True, GRAY)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y_pos))
            y_pos += 40

    def draw_high_scores(self):
        self.screen.blit(self.background, (0, 0))
        font = pygame.font.Font(None, 36)
        title = font.render("High Scores", True, WHITE)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 50))

        scores = self.load_scores()
        y_pos = 120
        for i, score in enumerate(scores[:5]):
            text = pygame.font.Font(None, 24).render(f"{i + 1}. {score}", True, GRAY)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y_pos))
            y_pos += 30

    def load_scores(self):
        try:
            with open("scores.json", "r") as f:
                return json.load(f)
        except:
            return []

    def save_score(self):
        scores = self.load_scores()
        scores.append(self.score)
        scores.sort(reverse=True)
        with open("scores.json", "w") as f:
            json.dump(scores[:10], f)

    def get_play_time(self):
        return pygame.time.get_ticks() - self.start_time

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_game()
            if event.type == pygame.KEYDOWN:
                if self.show_menu:
                    self.handle_menu_keys(event.key)
                elif self.game_over:  # Отдельная обработка для Game Over
                    if event.key == pygame.K_RETURN:
                        self.reset_game()
                        self.game_over = False
                    elif event.key == pygame.K_ESCAPE:
                        self.show_menu = True
                        self.reset_game()
                else:
                    self.handle_game_keys(event.key)

    def handle_menu_keys(self, key):
        if key == pygame.K_RETURN:
            self.show_menu = False
        elif key == pygame.K_h:
            self.show_high_scores = True
        elif key == pygame.K_q:
            self.quit_game()

    def handle_game_keys(self, key):
        if key == pygame.K_p:
            self.toggle_pause()
        elif not self.paused and not self.game_over:
            self.handle_game_actions(key)

    def handle_game_actions(self, key):
        if key == pygame.K_LEFT:
            self.move_piece(-1, 0)
        elif key == pygame.K_RIGHT:
            self.move_piece(1, 0)
        elif key == pygame.K_DOWN:
            self.move_piece(0, 1)
        elif key == pygame.K_UP:
            self.rotate_piece()
        elif key == pygame.K_SPACE:
            self.drop_piece()
        elif key == pygame.K_ESCAPE:
            self.show_menu = True
            self.game_over = False
            self.reset_game()

    def toggle_pause(self):
        """Переключение паузы (фоновая музыка удалена)"""
        self.paused = not self.paused
        # Код управления фоновой музыкой удален

    def move_piece(self, dx, dy):
        new_x = self.current_piece.x + dx
        new_y = self.current_piece.y + dy
        if not self.check_collision(self.current_piece.shape, new_x, new_y):
            self.current_piece.x = new_x
            self.current_piece.y = new_y
            self.sounds['Move'].play()

    def rotate_piece(self):
        new_shape, new_textures = self.current_piece.rotate()
        if not self.check_collision(new_shape, self.current_piece.x, self.current_piece.y):
            self.current_piece.shape = new_shape
            self.current_piece.textures = new_textures
            self.sounds['Rotate'].play()

    def drop_piece(self):
        while not self.check_collision(self.current_piece.shape,
                                       self.current_piece.x,
                                       self.current_piece.y + 1):
            self.current_piece.y += 1
        self.merge_piece()

    def update_particles(self):
        for particle in self.particles[:]:
            particle.update()
            if particle.life <= 0:
                self.particles.remove(particle)

    def draw_game(self):
        self.screen.blit(self.background, (0, 0))
        self.draw_grid()
        self.draw_piece(self.current_piece)
        self.draw_hud()
        for particle in self.particles:
            particle.draw(self.screen)
        if self.paused:
            self.draw_pause_overlay()
        if self.game_over:
            self.draw_game_over()

    def draw_pause_overlay(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))
        font = pygame.font.Font(None, 48)
        text = font.render("PAUSED", True, WHITE)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2))

    def draw_game_over(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 192))
        self.screen.blit(overlay, (0, 0))
        font = pygame.font.Font(None, 48)
        text = font.render("GAME OVER", True, WHITE)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 40))
        score = font.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score, (SCREEN_WIDTH // 2 - score.get_width() // 2, SCREEN_HEIGHT // 2 + 20))

        # Новая строка с инструкцией
        restart_text = font.render("Press ENTER to restart", True, (200, 200, 200))
        self.screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2,
                                        SCREEN_HEIGHT // 2 + 80))
    def quit_game(self):
        pygame.quit()
        exit()

    def run(self):
        while True:
            self.handle_events()

            if self.show_menu:
                self.draw_menu()
            elif self.show_high_scores:
                self.draw_high_scores()
                keys = pygame.key.get_pressed()
                if keys[pygame.K_ESCAPE]:
                    self.show_high_scores = False
                    self.show_menu = True
            else:
                if not self.paused and not self.game_over:
                    self.update_game()
                self.draw_game()

            pygame.display.flip()
            self.clock.tick(60)

    def update_game(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_fall > self.fall_speed:
            self.last_fall = current_time
            if not self.check_collision(self.current_piece.shape,
                                        self.current_piece.x,
                                        self.current_piece.y + 1):
                self.current_piece.y += 1
            else:
                self.merge_piece()

        self.update_particles()


if __name__ == "__main__":
    game = Tetris()
    game.run()