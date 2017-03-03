#!/usr/bin/python
#-*- coding: utf-8 -*-
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
from thespian.actors import *
from game.actors.Settings import WS_URL
import websockets
import asyncio
from game.serializers import GameSerializer
import ujson


class UIManagerActor(ActorTypeDispatcher):
    """
    Declare an actor to send game states to the web UI via websockets.
    """

    def receiveMsg_Game(self, message, sender):
        """
        Upon receiving an instance of the Game model, broadcast it to all other clients.
        :param message: An instance of the Game model.
        :param sender: The ActorAddress of the sending Actor.
        :return: Nothing.
        """

        # Serialize the game and all its components
        serializer = GameSerializer(message)
        # Render the serialized data in json format
        rendered_data = ujson.dumps(serializer.data, ensure_ascii=False)
        # Send the game to all clients
        asyncio.get_event_loop().run_until_complete(self._send_data(rendered_data))

    @asyncio.coroutine
    def _send_data(self, game):
        """
        Define a websocket client for sending game state to the Web UI.
        :param game: A Json rendered string describing the game and all its components.
        :return: Nothing.
        """

        # Connect to the websocket server and send the game state
        try:
              ws = yield from websockets.connect(WS_URL)
              yield from ws.send(game)
              yield from ws.close()
        except:
            pass
