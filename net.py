#!/usr/bin/env python3
import torch
import numpy as np
from torch import nn

import random
import os
import sys
import pygame
from flappy_birds import Engine, Bird

class NeuralNetwork(nn.Module):
    def __init__(self, layers):
        super(NeuralNetwork, self).__init__()

        counts = [3,1]
        for layer in layers:
            counts.insert(-1, layer)

        counts = list(zip(counts,counts[1:]))
        layers = []
        for count in counts:
            layers.append(nn.Linear(count[0],count[1]))
            layers.append(nn.ReLU())

        layers.pop(-1)
        layers.append(nn.Sigmoid())

        self.linear_relu_stack = nn.Sequential(*layers)

    def forward(self, x):
        logits = self.linear_relu_stack(x)
        return logits

class MyBird(Bird):
    def jump(self):
        self.vy += self.jump_burst

    def get_input_array(self):
        length_scale = 900
        y_dist1 = self.y - self.closest_pipe.y1
        y_dist2 = self.y - self.closest_pipe.y2
        f0 = self.vy / 10
        f2 = (length_scale - y_dist1) / length_scale
        f3 = (length_scale - y_dist2) / length_scale
        inputs = torch.tensor([f0, f2, f3])
        return inputs


def main(cfg):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    seed = 0.1
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    
    FPS = int(cfg['FPS'])
    mode = cfg['difficulty']
    seed = int(cfg['seed'])

    model = NeuralNetwork(cfg['layers'])
    model.to(device)

    loss_fn = nn.BCELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)

    size_x = 1600
    size_y = 900

    batch_pred = []
    batch_y = []
    
    best_time = -1
    steps = -1

    if cfg['load_choice'] is True:
        model.load_state_dict(torch.load('best.pt'))

    pygame.init()
    screen = pygame.display.set_mode((size_x, size_y), pygame.SRCALPHA, 32)
    clock = pygame.time.Clock()

    # Loop to restart automatically on death
    try:
        while True:
            my_bird = MyBird()
            game = Engine(size_x, size_y, [my_bird], mode=mode, seed=seed)

            # Main game loop
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()

                if my_bird.closest_pipe is not None:
                    inp = my_bird.get_input_array().to(device)
                    pred = model(inp)
                    if pred.item() >= 0.5:
                        my_bird.jump()
                else:
                    pred = None

                game.update()
                game.draw(screen)
                pygame.display.flip()
                clock.tick(FPS)

                if pred is not None:
                    # Neural Net training
                    y_dist = (my_bird.closest_pipe.y1 + my_bird.closest_pipe.y2)/2 - my_bird.y
                    y = torch.tensor([0.5 - (y_dist/size_y)], device=device)

                    batch_y.append(y)
                    batch_pred.append(pred)

                    if not game.has_alive_birds:
                        steps += 1

                        pred_tens = torch.stack([batch_pred[-1]]).to(device)
                        y_tens = torch.stack([batch_y[-1]]).to(device)
                        loss = loss_fn(pred_tens, y_tens)
                        optimizer.zero_grad()
                        loss.backward()
                        optimizer.step()

                        batch_pred = []
                        batch_y = []

                        print(f"Input: {inp}")
                        print(f"Prediction: {pred.item()}, Y: {y} Loss: {loss.item()}")
                        print(f"Training step: {steps}")
                        print('=====')
                        break

    except KeyboardInterrupt:
        choice = input("Save model?(y/n)")
        if choice.lower().startswith("y"):
            torch.save(model.state_dict(), 'best.pt')

if __name__=="__main__":
    cfg = {
        'FPS': 200,
        'seed': 1,
        'difficulty': 'medium',
        'layers': [100],
        'activation': 'ReLU',
        'load_choice': True
    }

    main(cfg)
