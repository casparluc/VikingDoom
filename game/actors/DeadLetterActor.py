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
from game.actors.SupervisorActor import SupervisorActor
from game.actors.utils import format_msg
from game.actors.Settings import LOOKUP_NAME, SUPERVISOR_NAME


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

    def receiveMessage(self, msg, sender):
        """
        When receiving a dead letter send a message to the
        :param msg: A DeadEnvelope containing the undelivered message and the address of the dead target.
        :param sender: ActorAddress of the ActorSystem.
        :return: Nothing.
        """

        # Make sure the message is a dead envelope
        if isinstance(msg, DeadEnvelope):
            # Ask for the lookup actor
            lookup = self.createActor(LookupActor, globalName=LOOKUP_NAME)

            # Send a dead action to the lookupActor to make sure any dead game has been unregistered
            message = format_msg('dead', data={'addr': msg.deadAddress})
            self.send(lookup, message)

            # The same goes for the supervisor, ensuring dead game are not considered as playing any more
            supervisor = self.createActor(SupervisorActor, globalName=SUPERVISOR_NAME)
            self.send(supervisor, message)
        elif isinstance(msg, str) and msg == 'init':
            # Declare the actor as handler for dead letters
            self.handleDeadLetters(startHandling=True)
