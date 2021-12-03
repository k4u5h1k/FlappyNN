import random
import pygame
import numpy as np


class Engine:

    dt = 2
    n_pipes = 5
    background_color = (150, 200, 220)

    def __init__(self, size_x, size_y, birds, mode='easy', seed=None):
        if seed is None:
            seed = random.randint(0, 1000000000)
        self.rs = np.random.RandomState(seed)

        self.size_x = size_x
        self.size_y = size_y
        self.birds = birds
        self.time = 0
        self.setup_mode(mode)
        self.initialize_random_pipes()

    @property
    def has_alive_birds(self):
        return any([bird.is_alive for bird in self.birds])

    def setup_mode(self, mode):
        self.mode = mode
        self.x_range = (900, 1000)
        if mode == 'easy':
            self.spacing_range = (200, 250)
        elif mode == 'medium':
            self.spacing_range = (150, 200)
        elif mode == 'hard':
            self.spacing_range = (140, 150)
        elif mode == 'impossible':
            self.spacing_range = (120, 130)
        else:
            raise ValueError('mode should be easy, medium, hard or impossible.')

    def initialize_random_pipes(self):
        """ setup first pipes """
        self.pipes = []

        # first pipe is easy
        pipe1 = Pipe(x=1400, y1=500, max_y=self.size_y, spacing=250)
        pipe1.index = 0

        self.pipes.append(pipe1)
        self.add_and_remove_pipes()

    def add_and_remove_pipes(self):

        # remove pipes left of screen
        keep_pipes = []
        for pipe in self.pipes:
            if pipe.x + pipe.width > 0:
                keep_pipes.append(pipe)
        self.pipes = keep_pipes

        # add new pipes until n_pipes
        while len(self.pipes) < self.n_pipes:
            x, y, spacing = self.generate_random_pipe_data()
            x_previous = self.pipes[-1].x
            x += x_previous
            pipe = Pipe(x, y, self.size_y, spacing)
            pipe.index = self.pipes[-1].index + 1
            self.pipes.append(pipe)

    def generate_random_pipe_data(self):
        min_pipe_height = 65
        x = int(self.rs.uniform(*self.x_range))
        spacing = int(self.rs.uniform(*self.spacing_range))
        y = int(self.rs.uniform(min_pipe_height+spacing, self.size_y-min_pipe_height))
        return x, y, spacing

    def update(self):
        self.time += self.dt
        self.add_and_remove_pipes()

        for pipe in self.pipes:
            pipe.update(self.dt)

        # find closest pipe to birds
        possible_pipes = [pipe for pipe in self.pipes if pipe.x+pipe.width > Bird.x-Bird.radius]
        closest_pipe = min(possible_pipes, key=lambda pipe: pipe.x)
        for bird in self.birds:
            if bird.is_alive:
                bird.update(self.dt, closest_pipe)
            y_dist = abs((closest_pipe.y1 + closest_pipe.y2)/2 - bird.y)
            bird.closest_pipe = closest_pipe
            bird.y_dist_to_pipe = y_dist

        # collision
        for bird in self.birds:
            if bird.is_alive:
                y_center = bird.center[1]
                if y_center - bird.radius <= 0:
                    bird.is_alive = False
                if y_center + bird.radius > self.size_y:
                    bird.is_alive = False
                if closest_pipe.collide(bird):
                    bird.is_alive = False

    def draw(self, screen, draw_status=False):
        screen.fill(self.background_color)

        for pipe in self.pipes:
            if (0 < pipe.x + pipe.width) and (pipe.x < self.size_x):
                pipe.draw(screen)

        for bird in self.birds:
            if bird.is_alive:
                bird.draw(screen)

        x, y = 20, 30
        font = pygame.font.SysFont('timesnewroman', 40, bold=True)
        text = font.render(f'Mode: {self.mode.title()} | Score {self.birds[0].time_alive//100}', False, (0, 0, 0))
        screen.blit(text, (x, y))


class Pipe:

    color = (40, 40, 40, 255)
    color = (20, 120, 20)
    width = 200
    speed = 3

    def __init__(self, x, y1, max_y, spacing):
        """
        y1 is upper position of lower pipe
        y2 is lower position of upper pipe
        spacing is distance between them
        """

        self.x = x
        self.y1 = y1
        self.y2 = self.y1 - spacing
        self.max_y = max_y

        self.upper_rect = pygame.rect.Rect(self.x, 0, self.width, self.y2)
        self.lower_rect = pygame.rect.Rect(self.x, self.y1, self.width, max_y)

    def update(self, dt):
        self.x -= self.speed * dt
        self.upper_rect.x = self.x
        self.lower_rect.x = self.x

    def draw(self, screen):
        self._draw_rect(screen, self.upper_rect)
        self._draw_rect(screen, self.lower_rect)

        font = pygame.font.SysFont('timesnewroman', 60)
        text = font.render(str(self.index), False, (255, 255, 255))
        text_size, _ = text.get_size()
        x_left = self.x + (self.width - text_size)/2
        screen.blit(text, (x_left, self.max_y-65))

    def _draw_rect(self, screen, rect):
        if False:
            pygame.draw.rect(screen, self.color, rect)
        else:
            border = 5
            rect2 = rect.copy()
            rect2.x += border
            rect2.width -= 2*border
            if rect2.y == 0:
                rect2.height -= border
            else:
                rect2.y += border

            pygame.draw.rect(screen, (0, 0, 0), rect)
            pygame.draw.rect(screen, self.color, rect2)

    def collide(self, bird):
        if self.lower_rect.colliderect(bird.rect):
            return True
        if self.upper_rect.colliderect(bird.rect):
            return True
        return False


class Bird:
    color = pygame.Color(80, 80, 200, 100)
    radius = 20
    side = 2 * radius
    thickness = 4
    x = 550

    jump_burst = -4.0
    gravity = 0.04

    def __init__(self, start_y=450):
        """ x, y is topleft """
        self.y = start_y
        self.vy = 0
        self.time_alive = 0
        self.is_alive = True
        self.rect = pygame.rect.Rect(self.x, self.y, self.side, self.side)
        self.closest_pipe = None

    @property
    def center(self):
        return self.rect.center

    def update(self, dt, closest_pipe):
        self.time_alive += dt
        self.vy += self.gravity*dt
        self.y += self.vy * dt
        self.rect.y = self.y

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.center, self.radius, self.thickness)

    def reset(self, y=450):
        self.vy = 0
        self.y = y
        self.time_alive = 0
        self.is_alive = True
