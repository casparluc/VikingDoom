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
from game.actors.utils import extract_msg, format_msg
from collections import defaultdict
from game.actors.LoggingActor import LoggingActor
from game.actors.Settings import LOGGING_NAME, LOOKUP_NAME
import logging


class PlayerLookupActor(ActorTypeDispatcher):
    """
    Define an actor to lookup for player actor ActorAddress for a given user and a given player.
    """

    def __init__(self):
        """
        Declare a lookup table for the player actors.
        """

        # Initialize the parent class
        super(PlayerLookupActor, self).__init__()

        # Declare the lookup table as a defaultdict
        self._table = defaultdict(dict)

    def receiveMsg_dict(self, message, sender):
        """
        Look for the ActorAddress corresponding to a given user in a given game.
        :param message: A formatted dictionary.
        :param sender: The ActorAddress of the sending Actor.
        :return: Nothing.
        """

        log = logging.getLogger(__name__)
        # Extract the content of the message
        action, data, orig = extract_msg(message)

        # Get the game and user codes
        game_code = data.get('game_code', None)
        user_code = data.get('user_code', None)
        log.debug("Received: game_code {} and user_code {}".format(game_code, user_code))
        if game_code is not None and user_code is not None:
            if action == 'look':
                log.debug("Looking for game {} and user {} in {}".format(game_code, user_code, self._table))
                # Look for the player address in the table
                game = self._table.get(game_code, None)
                if game is not None:
                    # Get the player's address
                    addr = game.get(user_code, None)
                    log.debug("Found the player's address {}".format(addr))
                    if addr is not None:
                        # And send the address back
                        self.send(sender, addr)
                    else:
                        # Forward the message to the game
                        lookup = self.createActor('game.actors.LookupActor', globalName=LOOKUP_NAME)
                        self.send(lookup, format_msg('player_addr', data={'game_code': game_code, 'user_code': user_code},
                                                     orig=sender))
                else:
                    self.send(sender, None)
            elif action == 'save':
                # Get the address
                act_addr = data.get('addr')
                log.debug("Saving game {}, user {} at address {}".format(game_code, user_code, act_addr))
                # Save the address
                if act_addr is not None:
                    self._table[game_code].update({user_code: act_addr})
                log.debug("Updated lookup table {}".format(self._table))
            elif action == 'remove':
                log.debug("User {} has been terminated".format(user_code))
                # Simply remove the address from the table
                self._table[game_code].pop(user_code, None)
            elif action == 'dead':
                log.debug("Game {} has died.".format(game_code))
                # Remove the game from the table
                self._table.pop(game_code, None)
        else:
            self.send(sender, None)
