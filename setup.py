#!/usr/bin/python

from distutils.core import setup

setup(
    name="VikingDoom",
    version="2.0.0",
    description="The Viking Doom server and game engine",
    url="https://github.com/casparluc/VikingDoom",
    author="Luc Caspar",
    author_email="LCaspar1@sheffield.ac.uk",
    packages=["Vikingdoom", "game", "game.actors", "bot"],
    requires=["Django", "djangorestframework", "coreapi", "mysqlclient", "websockets", "requests", "thespian", "ujson", "setproctitle"],
    package_data={"game": [
        "migrations/*",
        "templates/*",
        "logs/*",
        "logs/game_states/*",
        "static/game/fonts/*",
        "static/game/images/map/*",
        "static/game/images/site/*",
        "static/game/images/sprites/*",
        "static/game/images/sprites/blue/*",
        "static/game/images/sprites/blue/bow/*",
        "static/game/images/sprites/blue/drink/*",
        "static/game/images/sprites/blue/fight/*",
        "static/game/images/sprites/blue/walk/*",
        "static/game/images/sprites/brown/*",
        "static/game/images/sprites/brown/bow/*",
        "static/game/images/sprites/brown/drink/*",
        "static/game/images/sprites/brown/fight/*",
        "static/game/images/sprites/brown/walk/*",
        "static/game/images/sprites/green/*",
        "static/game/images/sprites/green/bow/*",
        "static/game/images/sprites/green/drink/*",
        "static/game/images/sprites/green/fight/*",
        "static/game/images/sprites/green/walk/*",
        "static/game/images/sprites/red/*",
        "static/game/images/sprites/red/bow/*",
        "static/game/images/sprites/red/drink/*",
        "static/game/images/sprites/red/fight/*",
        "static/game/images/sprites/red/walk/*",
        "static/game/scripts/*",
        "static/game/style/*"
    ],
        "bot": ["logs/*"],
    },
    data_files=[('', ['manage.py', 'robots.txt'])]
)
