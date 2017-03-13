#!/usr/bin/python
# -*- coding: utf-8 -*-

# Make sure we can use django in this script
import os
import sys
from django.conf import settings
from django import setup

# Add Viking Doom to the python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# Import the app settings
import Vikingdoom.settings

# Configure the app
if not settings.configured:
    settings.configure(default_settings=Vikingdoom.settings)
# Let django work its magic
setup()

# Rest of the import statements
from game.actors.LookupActor import LookupActor
from game.actors.PlayerLookupActor import PlayerLookupActor
from game.actors.SupervisorActor import SupervisorActor
from game.actors.UIManagerActor import UIManagerActor
from game.actors.LoggingActor import LoggingActor
from game.actors.Settings import LOGGING_NAME, LOOKUP_NAME, PLAYER_LOOKUP_NAME, SUPERVISOR_NAME, UI_MANAGER_NAME, WS_SERVER_HOST, WS_SERVER_PORT
from game.actors.utils import format_msg
from thespian.actors import *
import websockets
from websockets.exceptions import ConnectionClosed
import asyncio
from signal import SIGINT, SIGTERM

# Keep track of the client connected to the websocket server
REGISTERED_WS_CLT = set()
WS_SERVER = None
ASYNC_LOOP = None
ACTOR_SYSTEM = None


# Declare function necessary for handling request on the websocket server and shutting down both the server and actor system
def unregister(ws):
    """
    Simply remove the websocket from the set of registered client.
    :param ws: The websocket instance to remove.
    :return: Nothing.
    """
    global REGISTERED_WS_CLT

    # Try to remove the instance
    try:
        REGISTERED_WS_CLT.remove(ws)
    except KeyError:
        pass


def stop():
    """
    Stop the async event loop and websocket server, and shut down the ActorSystem.
    :return: Nothing.
    """
    global WS_SERVER, ASYNC_LOOP, ACTOR_SYSTEM

    # Wait for the server to close all connections gracefully
    WS_SERVER.wait_closed()
    # Stop the event loop
    ASYNC_LOOP.stop()
    # Shut the ActorSystem down
    ACTOR_SYSTEM.shutdown()


@asyncio.coroutine
def handler(ws, path):
    """
    Handler function for request arriving at the websocket server.
    :param ws: A websocket instance.
    :param path: The path requested upon connection. Only: '/consume' and '/produce' are available. All else is ignored.
    :return: Nothing.
    """
    global REGISTERED_WS_CLT

    # If the client is a simple consumer
    if path == '/consume':
        # Record its websocket
        REGISTERED_WS_CLT.add(ws)
        # And simply keep the connection alive
        while True:
            yield from asyncio.sleep(5)  # Keep alive ping is sent only every 5 seconds
            try:
                # Ping the client
                yield from ws.ping()
            except ConnectionClosed:
                # And unregister in case it quit or the connection was somehow lost
                unregister(ws)

    elif path == '/produce':  # If the client is a producer
        # Wait for the game state to arrive completely
        game_state = yield from ws.recv()
        # Broadcast the game state to all clients
        for sock in set(REGISTERED_WS_CLT):
            try:
                yield from sock.send(game_state)
            except ConnectionClosed:
                # Remove the client if the connection was lost
                unregister(sock)


def main():
    global WS_SERVER, ASYNC_LOOP, ACTOR_SYSTEM
    # Initialize the ActorSystem
    ACTOR_SYSTEM = ActorSystem("multiprocTCPBase", logDefs=Vikingdoom.settings.LOGGING)

    # Initialize the named Supervisor, Lookup, Logging and UIManager actors
    ACTOR_SYSTEM.createActor(SupervisorActor, globalName=SUPERVISOR_NAME)
    lookup = ACTOR_SYSTEM.createActor(LookupActor, globalName=LOOKUP_NAME)
    ACTOR_SYSTEM.tell(lookup, format_msg('init'))
    ACTOR_SYSTEM.createActor(PlayerLookupActor, globalName=PLAYER_LOOKUP_NAME)
    ACTOR_SYSTEM.createActor(LoggingActor, globalName=LOGGING_NAME)
    ACTOR_SYSTEM.createActor(UIManagerActor, globalName=UI_MANAGER_NAME)

    # Declare the websocket server
    start_srv = websockets.serve(handler, WS_SERVER_HOST, WS_SERVER_PORT)
    ASYNC_LOOP = asyncio.get_event_loop()
    WS_SERVER = ASYNC_LOOP.run_until_complete(start_srv)

    # Add a signal handler to gracefully shutdown the system from the command line
    ASYNC_LOOP.add_signal_handler(SIGINT, stop)
    ASYNC_LOOP.add_signal_handler(SIGTERM, stop)

    # Let the websocket server run until the ragnarok
    ASYNC_LOOP.run_forever()

if __name__ == "__main__":
    main()
