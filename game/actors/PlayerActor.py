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
from thespian.transient import transient_idle
from game.actors.utils import extract_msg, format_msg
from datetime import timedelta


@transient_idle(exit_delay=timedelta(seconds=30))
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
            self._player_state = data
        elif action == 'update':
            # Update the player object
            self._player_state = data
        elif action == 'next_action':
            # Check the state of the player
            if self._parent is None or self._player_state not in ['P', 'D']:
                # If the game is finished or the player terminated we might as well tell him
                if self._player_state in ['T', 'F']:
                    self.send(sender, None)
                else:
                    self.send(sender, format_msg('error', data="The game has not begun yet."))
            else:
                self.send(self._parent, format_msg('next_action', data=data, orig=sender))
