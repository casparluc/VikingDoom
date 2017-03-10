#!/usr/bin/python
# -*- coding: utf-8 -*-

# Make sure we can use django in this script
import os
import sys
from django.conf import settings
from django import setup

# Add Viking Doom to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Import the app settings
import Vikingdoom.settings

# Configure the app
if not settings.configured:
    settings.configure(default_settings=Vikingdoom.settings)
# Let django work its magic
setup()

# Rest of the import statements
from game.models import DEFAULT_PLAYER_HEALTH

# Declare all required global names
SUPERVISOR_NAME = "Supervisor"
LOOKUP_NAME = "Lookup"
LOGGING_NAME = 'Logging'
UI_MANAGER_NAME = "UIManager"
PLAYER_LOOKUP_NAME = "PlayerLookup"

MAX_GAMES = 2

WS_SERVER_HOST = 'www.vikingdoom.com'
WS_SERVER_PORT = 8765
WS_URL = "ws://{}:{}/produce".format(WS_SERVER_HOST, WS_SERVER_PORT)

NEIGHBOUR_TILES = {'E': (1, 0), 'S': (0, 1), 'W': (-1, 0), 'N': (0, -1), 'I': (0, 0)}
MAX_TURN = 1000
POTION_MARKET_VALUE = 10
MAX_PLAYER_STRENGTH = 25
DRAGON_GOLD = 500
DRAGON_STRENGTH = DEFAULT_PLAYER_HEALTH / 4
DRAGON_HEALTH = 10000
ORC_STRENGTH = 5
MAX_ENEMIES = 10
MAX_ITEMS = 10
RANGE_MARKET_U = [1, 2]
RANGE_MARKET_P = [2, 4]
RANGE_MINE = [5, 10]
BASE_GAME_URL = "http://www.vikingdoom.com/game/play"
BOARD_CONFIG_FILES = [
    os.path.join(Vikingdoom.settings.BASE_DIR, 'game/maps/json/0.json'), 
    os.path.join(Vikingdoom.settings.BASE_DIR, 'game/maps/json/1.json'), 
    os.path.join(Vikingdoom.settings.BASE_DIR, 'game/maps/json/2.json'), 
    os.path.join(Vikingdoom.settings.BASE_DIR, 'game/maps/json/3.json'), 
    os.path.join(Vikingdoom.settings.BASE_DIR, 'game/maps/json/4.json'), 
    os.path.join(Vikingdoom.settings.BASE_DIR, 'game/maps/json/5.json'), 
    os.path.join(Vikingdoom.settings.BASE_DIR, 'game/maps/json/6.json'), 
    os.path.join(Vikingdoom.settings.BASE_DIR, 'game/maps/json/7.json'), 
    os.path.join(Vikingdoom.settings.BASE_DIR, 'game/maps/json/8.json'), 
    os.path.join(Vikingdoom.settings.BASE_DIR, 'game/maps/json/9.json'), 
    os.path.join(Vikingdoom.settings.BASE_DIR, 'game/maps/json/10.json'),
    os.path.join(Vikingdoom.settings.BASE_DIR, 'game/maps/json/11.json')
]
