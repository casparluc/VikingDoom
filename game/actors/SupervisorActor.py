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
from thespian.actors import *
from collections import deque
from game.actors.utils import format_msg, extract_msg
from game.actors.Settings import MAX_GAMES, LOOKUP_NAME


class SupervisorActor(ActorTypeDispatcher):
    """
    Define a supervisor that manages the game queue. Allowing only a certain number of games to play at a time.
    And waking up initialized games when other terminate.
    """

    def __init__(self):
        """
        Initialize a queue of waiting games and a set of playing games.
        """

        # Initialize the parent class
        super(SupervisorActor, self).__init__()

        # Initialize the required attributes
        self._waiting = deque()  # Contains game codes
        self._playing = set()  # Contains game codes
        self._ui_connected = None

    def receiveMsg_dict(self, message, sender):
        """
        Define the action to perform upon reception of a message of type dict
        :param message: A dictionary message formatted as follow: {action: ..., data: ..., orig: ...}
        :param sender: The ActorAddress of the sending Actor
        :return: Nothing
        """

        # Extract action and data from the message for easy access
        action, data, orig = extract_msg(message)

        if action == "full":
            # Check if the limit of playing game has been reached
            game_code = data.get('code')
            if game_code is not None:
                if len(self._playing) >= MAX_GAMES:
                    # Add the address of the sender (the GameActor) to the queue of waiting games
                    self._waiting.append(game_code)
                else:
                    # Add the player to the set of playing games
                    self._playing.add(game_code)
                    # Launch the next game
                    self.send(self.myAddress, format_msg('next', data={'addr': sender, 'code': game_code}))
        elif action == "dead":
            # Upon death of a game, remove it from the playing set and launch the next game from the waiting queue
            game_code = data.get('game')
            if game_code in self._playing:
                self._playing.remove(game_code)

            # Check if the game was connected to the ui
            if self._ui_connected == game_code:
                self._ui_connected = None

            # Send a request to the lookup actor for the address of the next game
            if len(self._waiting) > 0:
                next_game = self._waiting.popleft()
                lookup = self.createActor('game.actors.LookupActor', globalName=LOOKUP_NAME)
                self.send(lookup, format_msg('addr', data={'code': next_game}))

        elif action == 'next':
            # Extract the required information from the data
            game_addr = data.get('addr', None)
            game_code = data.get('code', None)

            if game_addr is not None and game_code is not None:
                # Tell the game to connect to the ui
                if self._ui_connected is None:
                    self._ui_connected = game_code
                    self.send(game_addr, format_msg('ui'))

                # Tell the next game to play
                self.send(game_addr, format_msg('play'))

                # Add the game to the set of playing games
                self._playing.add(game_code)
