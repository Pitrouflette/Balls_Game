import pygame
import pygame.midi
import random
import math
from mido import MidiFile

IMAGE = False
MUSIC_ON = False
NAMES = ["YES", "NO"]
QUESTION = ""
MUSIC = "Wii"
COLORS = [(0, 0, 255), (0, 255, 0)]
FPS = 60
HEIGHT = 800
WIDTH = 800
TOTAL_FRAME = 60 * 61
BALL_COUNT = 2
BALL_RADIUS = 20
CIRCLE_ROTATION_SPEED = 0.01
CIRCLE_GAP_SIZE = 0.5
CIRCLE_COUNT = 10
FONT_SIZE = 36
GRAVITY = 0.15

pygame.init()
pygame.midi.init()
pygame.mixer.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((HEIGHT, WIDTH))
font = pygame.font.SysFont(None, FONT_SIZE)
bounce_sound = pygame.mixer.Sound("musics/bounce.mp3")

class MidiNotePlayer:
    def __init__(self, midi_path):
        self.port = pygame.midi.Output(0)
        self.notes = []
        self.index = 0
        self.channel = 0
        try:
            mid = MidiFile(midi_path)
            for msg in mid:
                if not msg.is_meta and msg.type == 'note_on' and msg.velocity > 0:
                    self.notes.append((msg.note, msg.velocity))
        except Exception as e:
            print(f"Erreur chargement MIDI: {e}")

    def play_next(self):
        if not self.notes:
            return
        for _ in range(1):
            note, velocity = self.notes[self.index]
            self.port.note_on(note, velocity, self.channel)
            self.index = (self.index + 1) % len(self.notes)

    def close(self):
        self.port.close()

midi_player = MidiNotePlayer(f"musics/{MUSIC}.mid")

def calculate_circle_radii():
    max_radius = min(WIDTH, HEIGHT) // 2 - 50
    min_radius = 100
    return [min_radius + (max_radius - min_radius) * i / (CIRCLE_COUNT - 1) for i in range(CIRCLE_COUNT)]

def load_circular_image(path, radius):
    try:
        image = pygame.image.load(path).convert_alpha()
        image = pygame.transform.smoothscale(image, (radius * 2, radius * 2))
        circle_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(circle_surface, (255, 255, 255, 255), (radius, radius), radius)
        image.blit(circle_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        return image
    except Exception as e:
        print(f"Erreur image {path}: {e}")
        surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surface, (255, 255, 255, 255), (radius, radius), radius)
        return surface

class Ball:
    def __init__(self, x, y, name, color):
        self.color = color
        self.name = name
        self.x = x
        self.y = y
        self.vx = random.uniform(5, 7)
        self.vy = random.uniform(5, 7)
        self.score = 0
        self.image = load_circular_image(f"images/{self.name}.png", BALL_RADIUS)

    def update(self):
        self.vy += GRAVITY
        self.x += self.vx
        self.y += self.vy

    def draw(self):
        if IMAGE:
            screen.blit(self.image, (int(self.x - BALL_RADIUS), int(self.y - BALL_RADIUS)))
            text = font.render(str(self.score), True, (255, 255, 255))
            screen.blit(text, (self.x - 10, self.y - BALL_RADIUS - 20))
        else:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), BALL_RADIUS)
            text = font.render(str(self.score), True, (255, 255, 255))
            screen.blit(text, (self.x - 10, self.y - 30))

class Circle:
    def __init__(self, radius):
        self.radius = radius
        self.angle = 0
        self.start_angle = (self.angle - CIRCLE_GAP_SIZE) % (2 * math.pi)
        self.end_angle = (self.angle % (2 * math.pi))
        self.broken = False
        self.rect = (WIDTH // 2 - self.radius, HEIGHT // 2 - self.radius, self.radius * 2, self.radius * 2)

    def draw(self):
        if self.broken:
            return
        pygame.draw.arc(screen, (255, 0, 0), self.rect, 2 * math.pi - self.start_angle, 2 * math.pi - self.end_angle, 2)

    def update(self):
        self.angle = (self.angle + CIRCLE_ROTATION_SPEED * self.radius / 150) % (2 * math.pi)
        self.start_angle = (self.angle - CIRCLE_GAP_SIZE) % (2 * math.pi)
        self.end_angle = (self.angle % (2 * math.pi))

    def check_collision(self, ball):
        if self.broken:
            return False

        distance = math.sqrt((WIDTH // 2 - ball.x) ** 2 + (HEIGHT // 2 - ball.y) ** 2)
        ball_angle = math.atan2(ball.y - HEIGHT // 2, ball.x - WIDTH // 2)

        if abs(distance - self.radius) <= BALL_RADIUS:
            if self.start_angle < ball_angle < self.end_angle:
                self.broken = True
                ball.score += 1
                if MUSIC_ON:midi_player.play_next()
                else:bounce_sound.play()
                return True

            direction = (ball.x - WIDTH // 2, ball.y - HEIGHT // 2)

            normale = (direction[0] / distance, direction[1] / distance)
            vitesse = (ball.vx, ball.vy)
            dot_product = vitesse[0] * normale[0] + vitesse[1] * normale[1]
            ball.vx = vitesse[0] - 2 * dot_product * normale[0]
            ball.vy = vitesse[1] - 2 * dot_product * normale[1]
            if MUSIC_ON:midi_player.play_next()
            else:bounce_sound.play()
            return True

        return False

balls = [Ball(WIDTH // 2, HEIGHT // 2, NAMES[i], COLORS[i]) for i in range(BALL_COUNT)]
circles = [Circle(i) for i in calculate_circle_radii()]

running = True
over = False
while running:
    screen.fill((0, 0, 0))

    if len(circles) == 0:
        winner_ball = balls[0]
        for ball in balls[1:]:
            if ball.score > winner_ball.score:
                winner_ball = ball
        text = font.render(f"The winner is : {winner_ball.name} !!", True, winner_ball.color)
        screen.blit(text, (WIDTH // 2 - text.get_width() // 2, HEIGHT // 2))
        over = True

    if not over:
        for circle in circles[:]:
            if circle.broken:
                circles.remove(circle)
                continue
            circle.update()
            circle.draw()

        for i, ball in enumerate(balls):
            ball.update()
            for circle in circles[:]:
                circle.check_collision(ball)
            ball.draw()

            x = (WIDTH // len(balls)) * i + (WIDTH // len(balls)) // 2
            text = font.render(f"{ball.name} : {ball.score}", True, ball.color)
            text_rect = text.get_rect(center=(x, 20))
            screen.blit(text, text_rect)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    clock.tick(FPS)
    pygame.display.flip()

pygame.quit()
midi_player.close()
pygame.midi.quit()