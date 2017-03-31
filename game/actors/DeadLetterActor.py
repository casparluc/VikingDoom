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
from game.actors.LookupActor import LookupActor
from game.actors.LoggingActor import LoggingActor
from game.actors.utils import format_msg, extract_msg
from game.actors.Settings import LOOKUP_NAME, LOGGING_NAME


class DeadLetterActor(Actor):
    """
    Define an actor for handling dead letters.
    """

    def __init__(self):
        """
        Declare the actor as being a DeadLetter handler.
        """

        # Initialize the parent class
        super(DeadLetterActor, self).__init__()

        # Declare a logger
        self._logger = None

    def receiveMessage(self, msg, sender):
        """
        When receiving a dead letter send a message to the
        :param msg: A DeadEnvelope containing the undelivered message and the address of the dead target.
        :param sender: ActorAddress of the ActorSystem.
        :return: Nothing.
        """

        # Make sure the message is a dead envelope
        if isinstance(msg, DeadEnvelope):
            # Send an error message to the logging actor
            self.send(self._logger, format_msg('error', data="{} - Received a dead letter from actor: {}, containing"
                                                             " the message: {}".format(__name__, msg.deadAddress,
                                                                                       msg.deadMessage)))
            # Ask for the lookup actor
            lookup = self.createActor(LookupActor, globalName=LOOKUP_NAME)

            # Send a dead action to the lookupActor to make sure any dead game has been unregistered
            message = format_msg('dead', data={'addr': msg.deadAddress})
            self.send(lookup, message)
            # Check if the dead message was sent from a view (ie: contains an orig)
            action, data, orig = extract_msg(msg.deadMessage)
            if orig is not None:
                # Simply send back None to the original sender
                self.send(orig, None)
        elif isinstance(msg, PoisonMessage):
            # This most probably means that the logging actor failed, so we should update its address
            self._logger = self.createActor(LoggingActor, globalName=LOGGING_NAME)
            # And put it to work
            self.send(self._logger, format_msg('error', data="{} - Received a poison message for"
                                                             " request: {} ({}).".format(__name__, msg.poisonMessage,
                                                                                         msg.details)))
        elif isinstance(msg, str) and msg == 'init':
            # Declare the actor as handler for dead letters
            self.handleDeadLetters(startHandling=True)
            # Declare the logging actor
            self._logger = self.createActor(LoggingActor, globalName=LOGGING_NAME)
