import pygame
import neat
import time
import os
import random
import pickle

pygame.font.init()
# Setting the width and height of the window
WIN_WIDTH = 500
WIN_HEIGHT = 900

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird1.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird2.png"))),
             pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png")))

STAT_FONT = pygame.font.SysFont("comicsans", 50)


# Class for the bird object (creates birds for the AI aspect)
class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25  # Used to tilt the bird to make it look like it is going up
    ROT_VEL = 20  # How much we will rotate on each frame
    ANIMATION_TIME = 5  # How fast or slow the bird would be flapping its wings

    def __init__(self, x, y):
        self.x = x  # x axis of the bird
        self.y = y  # y axis of the bird
        self.tilt = 0  # Represents each bird's tilt
        self.tick_count = 0  # deals with the physics of the bird
        self.vel = 0  # the velocity of the bird
        self.height = self.y
        self.img_count = 0  # Keeps track of which img, used in animation
        self.img = self.IMGS[0]  # References the list of bird images

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0  # Keeps track of when we last jumped
        self.height = self.y  # Keeps track of where the bird jumped from

    # Every single frame to move the bird
    def move(self):
        self.tick_count += 1  # Means a frame went by
        d = self.vel * self.tick_count + 1.5 * 3 * self.tick_count ** 2  # How many pixels up or down moved

        if d >= 16:
            d = 16

        if d < 0:
            d -= 2

        self.y = self.y + d

        # Tilting the bird upwards
        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION

        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL  # Rotates the bird by 90 degrees, makes it look like it is falling to the
                # ground

    def draw(self, win):
        self.img_count += 1

        # Checking what image to show based on current img
        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME * 2:  # Wings are leveled
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME * 3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME * 4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME * 4 + 1:
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME * 2

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 200  # the gap between the pipes
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
        self.gap = 100

        # Keeps track of where top and bottom of pipe is going to be drawn
        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False  # Checks to see if the bird has already passed by the pipe (collision purposes and AI)
        self.set_height()

    # function to see the height of the top, bottom pipe and distance between two pipes
    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    # Moving the pipes along with frame
    def move(self):
        self.x -= self.VEL

    # Drawing the pipes
    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    # Takes into account collisions, by using masks
    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        # Need to calculate the offset between the masks
        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # Finds the overlap of masks between the bird mask and the bottom pipe
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if t_point or b_point:
            return True

        return False


class Base:
    VEL = 5
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL
        # Cycling the background to make it look like it is moving
        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))


def draw_window(win, birds, pipes, base, score):
    win.blit(BG_IMG, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIN_WIDTH - 10 - text.get_width(), 10))

    base.draw(win)
    for bird in birds:
        bird.draw(win)

    pygame.display.update()  # Draws the game, displays and updates


# Runs the main loop of our game, genomes are just a bunch of incoming neural networks
def main(genomes, config):
    nets = []
    ge = []
    birds = []

    # Setting up a neural network for the genome, a bird object and keep track of the genome in a list
    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(23, 350))
        g.fitness = 0
        ge.append(g)

    base = Base(730)
    pipes = [Pipe(600)]
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()

    score = 0

    run = True
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # Quits the game
                run = False
                pygame.quit()
                quit()
        pip_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1
            
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))

            if output[0] > 0.5:
                bird.jump()

        add_pipe = False
        rem = []  # Stores the pipes that have been completed
        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness += 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)

            pipe.move()

        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(600))  # Change this number if the pipes should spawn closer

        for r in rem:
            pipes.remove(r)
        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()
        draw_window(win, birds, pipes, base, score)


# AI aspect of the game
def run(config_path):
    # Loading in the config file
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction,
                                neat.DefaultSpeciesSet, neat.DefaultStagnation,
                                config_path)

    # Set up the bird population
    p = neat.Population(config)

    # The under hood computations by the algorithm can now be seen
    p.add_reporter(neat.stdOutReporter(True))
    stats = neat.StatisticsReporter()
    p.add_reporter(stats)

    winner = p.run(main, 50)


if __name__ == "main":
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, "config-feedforward.txt")
    run(config_path)
