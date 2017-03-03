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
from thespian.troupe import troupe
from game.actors.utils import extract_msg
from game.serializers import  CustomGameSerializer
from django.core.mail import send_mail
import logging
import ujson


@troupe(idle_count=2)  # Define a troupe of actors with a minimum size of 2 and a maximum of 10
class LoggingActor(ActorTypeDispatcher):
    """
    Declare an actor which sole purpose is to dispatch log messages to the appropriate file and extract information
    from Game object to track game states over time.
    """

    def __init__(self):
        """
        Initialize the different logging facilities.
        """

        # Initialize the parent class
        super(LoggingActor, self).__init__()

        # Get the logging facilities for the actors
        self._debug = logging.getLogger("Game.dm.debug")
        self._info = logging.getLogger("Game.dm.info")
        self._warn = logging.getLogger("Game.dm.warn")
        self._error = logging.getLogger("Game.dm.error")

    def receiveMsg_Game(self, message, sender):
        """
        Upon reception of a message, simply log the full state of the game into its dedicated file.
        :param message: An instance of the Game model.
        :param sender: The ActorAddress of the sending Actor.
        :return: Nothing.
        """

        log = logging.getLogger(__name__)
        log.debug("Got a game instance {}".format(message.code))
        # Declare the game serializer
        serializer = CustomGameSerializer(message)

        # Write the game state to its dedicated file
        filename = os.path.join(Vikingdoom.settings.BASE_DIR, 'game/logs/game_states/game_{}.log'.format(message.code))
        with open(filename, "a") as f:
            ujson.dump(serializer.data, f)
            f.write("\n")

    def receiveMsg_dict(self, message, sender):
        """
        Send other messages to the log file corresponding to their level.
        :param message: A formatted dictionary containing the log level and log message.
        :param sender: The ActorAddress of the sending Actor.
        :return: Nohting.
        """

        log = logging.getLogger(__name__)
        log.debug("Got a message: {}".format(message))
        # Extract the content of the message
        action, data, orig = extract_msg(message)
        if action == 'debug':
            self._debug.debug(data)
        elif action == 'info':
            self._info.info(data)
        elif action == 'warn':
            self._warn.warning(data)
        elif action == 'error':
            self._error.error(data)
        elif action == 'exception':
            self._error.exception(data)
            send_mail(subject="Exception occurred in actor system", message=message,
                      from_email="actor_system@vikingdoom.com", recipient_list=[Vikingdoom.settings.ADMINS[0][0]])
        elif action == 'fatal':
            self._error.fatal(data)
            send_mail(subject="Fatal error occurred in actor system", message=message,
                      from_email="actor_system@vikingdoom.com", recipient_list=[Vikingdoom.settings.ADMINS[0][0]])
