#!/usr/bin/python
# -*- coding: utf-8 -*-
# Make sure we can use django in this script
import os
import sys
from thespian.actors import *
from django.conf import settings
from django import setup, db

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
from game.actors.GameActor import GameActor
from game.actors.utils import format_msg, extract_msg, code_generator
from game.models import Game


class CreateActor(ActorTypeDispatcher):
    """
    Define a simple actor that will create game actors and models.
    """

    def __init__(self):
        """
        Initialize the class' attributes.
        """
        
        # Run the initialization process of the parent class
        super(CreateActor, self).__init__()
        
        # Initialize the address of the parent
        self._parent = None

    def receiveMsg_dict(self, message, sender):
        """
        Define the action to perform upon reception of a message of type dict.
        :param message: A formatted dictionary: {action: ..., data: ..., orig: ...}
            Where action can take on the values:
                + new: Create a new gameActor Actor
                + parent: Store the ActorAddress of the parent
        :param sender: ActorAddress, the address of the sending actor.
        :return: Nothing.
        """

        action, data, orig = extract_msg(message)

        if action == 'parent':
            # Store the sender's address as the parent
            self._parent = sender
        elif action == 'new':
            # Generate a unique code
            game_code = code_generator()
            while Game.objects.filter(code__exact=game_code).count() > 0:
                game_code = code_generator()

            # Close all db connections so they do not get forked to child processes
            db.connections.close_all()
            # Create and initialize a new game actor
            game_addr = self.createActor(GameActor)
            self.send(game_addr, format_msg('init', data={'code': game_code}, orig=orig))

    def receiveMsg_ChildActorExited(self, message, sender):
        """
        Define the action to perform upon the death of a child actor.
        :param message: An instance of the ChildActorExited class, containing the childAddress attribute.
        :param sender: The ActorAddress corresponding to the ActorSystem. Can safely be ignored here.
        :return: Nothing.
        """

        # Send a message to the parent to remove the game from the lookup table
        msg = format_msg('dead', data={'addr': message.childAddress})
        self.send(self._parent, msg)
