#!/usr/bin/env python3
import pygame
import pygame_menu
from net import main

pygame.init()
surface = pygame.display.set_mode((1600, 900))

cfg  = {
    'FPS': 200,
    'seed': 1,
    'difficulty': 'medium',
    'layers': [100],
    'activation': 'ReLU',
    'load_choice': True
}

menu = pygame_menu.Menu('FlappyNN', 1600, 900,
       theme=pygame_menu.themes.THEME_GREEN)

def set_difficulty(value, difficulty):
    cfg['difficulty'] = value[0][0].lower()

def set_activation(value, activation):
    cfg['activation'] = value[0][0].lower()

def set_fps(value):
    cfg['FPS'] = value

def set_seed(value):
    cfg['seed'] = value

def set_layers(value):
    cfg['layers'] = eval(value)

def start_the_game():
    main(cfg)

def load_choice(value):
    if value is True:
        cfg['load_choice'] = False
        menu.remove_widget(menu.get_widget('load_choice'))
        menu.remove_widget(menu.get_widget('play'))
        menu.remove_widget(menu.get_widget('quit'))
        menu.add.text_input('FPS : ', default=cfg['FPS'], onchange=set_fps)
        menu.add.text_input('Seed : ', default=cfg['seed'], onchange=set_seed)
        menu.add.text_input('Hidden Layer Setup (in list) : ', default=str(cfg['layers']), onchange=set_layers)
        menu.add.selector('Difficulty : ', [('Medium', 1), ('Easy', 2), ('Hard', 3)], onchange=set_difficulty)
        menu.add.selector('Activation : ', [('ReLU', 1), ('SGD', 2), ('tanh', 3)], onchange=set_activation)
        menu.add.button('Play', start_the_game)
        menu.add.button('Quit', pygame_menu.events.EXIT)

menu.add.toggle_switch('Train model from scratch? ', 
        False,
        onchange=load_choice,
        toggleswitch_id='load_choice')

menu.add.button('Play', 
        start_the_game,
        button_id="play")

menu.add.button('Quit', 
        pygame_menu.events.EXIT,
        button_id="quit")

menu.mainloop(surface)

