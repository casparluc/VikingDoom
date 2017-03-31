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
from game.actors.utils import extract_msg, format_msg
from game.actors.Settings import LOGGING_NAME
from game.actors.LoggingActor import LoggingActor
from datetime import timedelta


class PlayerActor(ActorTypeDispatcher):
    """
    Define an actor managing a player in the game. It receives its input from the django view and send the next move to
    its gameActor parent.
    """

    def __init__(self):
        """
        Declare the various required attributes.
        """
        # Initialize the parent class
        super(PlayerActor, self).__init__()

        # Initialize the rest of the attributes
        self._parent = None
        self._logger = None
        self._alive = False
        self._player_state = None

    def receiveMsg_dict(self, message, sender):
        """
        Perform the appropriate action given the content of the message.
        :param message: A formatted dictionary.
        :param sender: The ActorAddress of the sending Actor (most probably a django view).
        :return: Nothing.
        """

        action, data, orig = extract_msg(message)
        if action == 'init':
            # Store the ActorAddress of the sender as the parent
            self._parent = sender
            # Store the player object
            # Routinely check that the player is still alive
            self.wakeupAfter(timePeriod=timedelta(seconds=30))
            self._logger = self.createActor(LoggingActor, globalName=LOGGING_NAME)

            # Save the player's state
            self._player_state = data
        elif action == 'update':
            # Update the player object
            self._player_state = data
        elif action == 'next_action':
            # Check the state of the player
            if self._parent is None or self._player_state not in ['P', 'D']:
                if self._player_state in ['T', 'F']:
                    self.send(sender, None)
                else:
                    self.send(sender, format_msg('error', data="The game has not begun yet."))
            else:
                self.send(self._parent, format_msg('next_action', data=data, orig=sender))

            # Make sure to notify the actor that the player is still alive
            self._alive = True

    def receiveMsg_WakeupMessage(self, message, sender):
        """
        A routine checking that the player is still alive. Called every 30 seconds.
        :param message: An instance of the WakeupMessage class.
        :param sender: The ActorAddress of the sending Actor.
        :return: Nothing.
        """

        if self._alive:
            # Switch back to dead until the next message
            self._alive = False
            self.wakeupAfter(timePeriod=timedelta(seconds=30))
        else:
            # The player did not get any message in the last 30 seconds better quit while you are ahead
            self.send(self.myAddress, ActorExitRequest())

    def receiveMsg_PoisonMessage(self, message, sender):
        """
        Handle messages that made the destination actor crash.
        :param message: An instance of the PoisonMessage class containing: poisonMessage, details.
        :param sender: The ActorAddress of the ActorSystem. Ignore it.
        :return: Nothing.
        """

        # The most likely occurrence of this happening is if the logging actor crashed, so update its address
        self._logger = self.createActor(LoggingActor, globalName=LOGGING_NAME)
        # And put it to work
        self.send(self._logger, format_msg('error', data="{} - Received a poison message for"
                                                         " request: {} ({}).".format(__name__, message.poisonMessage,
                                                                                     message.details)))
