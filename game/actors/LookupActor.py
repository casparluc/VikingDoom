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
from random import choice
from game.actors.CreateActor import CreateActor
from game.actors.SupervisorActor import SupervisorActor
from game.actors.PlayerLookupActor import PlayerLookupActor
from game.actors.utils import extract_msg, format_msg
from game.actors.Settings import SUPERVISOR_NAME, PLAYER_LOOKUP_NAME, LOGGING_NAME
from game.actors.LoggingActor import LoggingActor


class LookupActor(ActorTypeDispatcher):
    """
    Define an actor responsible for maintaining the link between a game code and its ActorAddress.
    """

    def __init__(self):
        """
        Simply initialize the dictionary of links between game code and ActorAddress.
        """

        # Call the initialization of the parent class
        super(LookupActor, self).__init__()

        # Initialize the address book - {game_code: actorAddress, ... }
        self._table = {}

        # Initialize a list of incomplete game (not all four players are present)
        self._incomplete = set()

        # Create a child CreateActor actor
        self._child = None

        # Initialize the logging actor
        self._logger = None

    def receiveMsg_dict(self, message, sender):
        """
        Receive and act upon a message of type dictionary. Possible actions are:
            + addr: sent by the django interface to request a lookup.
            + dead: sent by the createActor to unregister a gameActor ActorAddress
            + full: sent by a gameActor to remove it from the incomplete set
            + new: sent by the createActor once a gameActor has been created
        :param message: A dictionary formatted as follow: {action: ..., data: ..., orig: ...}
            Where action is one of the above actions, data is a dictionary containing the information necessary to
            complete the action and orig is the original sender if necessary
        :param sender: ActorAddress of the actor sending the message
        :return: Nothing
        """

        # Extract information from the message
        action, data, orig = extract_msg(message)
        if action == 'init':
            self._child = self.createActor(CreateActor)
            self.send(self._child, format_msg('parent'))
            self._logger = self.createActor(LoggingActor, globalName=LOGGING_NAME)
        elif action == 'dead':  # If a gameActor died
            # Simply remove it from the lookup table
            try:
                game_addr = data.get('addr')
                for code in dict(self._table):
                    if self._table[code] == game_addr:
                        self._table.pop(code)
                        # Notify the supervisor of the game's death
                        supervisor = self.createActor(SupervisorActor, globalName=SUPERVISOR_NAME)
                        self.send(supervisor, format_msg('dead', data={'game': code}))
                        # Notify the player lookup table of the game's death
                        lookup = self.createActor(PlayerLookupActor, globalName=PLAYER_LOOKUP_NAME)
                        self.send(lookup, format_msg('dead', data={'game_code': code}))
                        break
            except KeyError:
                pass
        elif action == 'full':
            game_code = data.get('code', None)
            # Remove the game from the incomplete set
            try:
                self._incomplete.remove(game_code)
            except KeyError:
                self.send(self._logger, format_msg('exception', data="{} -- Could not remove game {} from"
                                                                     " incomplete set {}".format(__name__,
                                                                                                 game_code,
                                                                                                 self._incomplete)))
                pass
        elif action == 'player_addr':
            game_code = data.get('game_code', None)
            user_code = data.get('user_code', None)

            # Get the address of the game corresponding to the game_code
            game_addr = self._table.get(game_code, None)
            if game_addr is not None:
                # Forward the message to the game in question
                self.send(game_addr, format_msg('player_addr', data={'user_code': user_code}, orig=orig))
            else:
                # Send back a None to the original sender
                self.send(orig, None)
        elif action == 'addr':
            code = data.get('code', None)
            if code is not None:
                # Send back the ActorAddress corresponding to the game
                self.send(sender, format_msg('next', data={'addr': self._table.get(code), 'code': code}))
            else:
                subscribed = data.get('subscribed', None)
                incomplete = [self._table[code] for code in self._incomplete]
                if subscribed is not None:
                    incomplete_unsubscribed = [game_addr for game_addr in incomplete if game_addr not in subscribed]
                else:
                    incomplete_unsubscribed = incomplete
                if len(incomplete_unsubscribed) == 0:
                    # Ask for the creation of a new game
                    self.send(self._child, format_msg('new', orig=sender))
                else:
                    # Send back the address of an incomplete game
                    game_addr = choice(incomplete_unsubscribed)
                    self.send(sender, game_addr)
        elif action == 'new':
            # Add the new game to the lookup tables and the set of incomplete games
            addr = data.get('addr')
            code = data.get('code')
            if addr is not None and code is not None:
                self._incomplete.add(code)
                self._table.update({code: addr})
