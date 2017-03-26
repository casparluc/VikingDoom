#!/usr/bin/python
# -*- coding: utf-8 -*-
# Make sure we can use django in this script
import os
import sys
from django.conf import settings
from django import setup
from django.core.exceptions import ObjectDoesNotExist
from django.db.transaction import commit

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
from datetime import timedelta
from random import choice, randint
import ujson
from math import floor
from thespian.actors import *
from game.models import *
from game.actors.UIManagerActor import UIManagerActor
from game.actors.SupervisorActor import SupervisorActor
from game.actors.PlayerLookupActor import PlayerLookupActor
from game.actors.PlayerActor import PlayerActor
from game.actors.utils import format_msg, extract_msg
from game.actors.Settings import *
from game.actors.LoggingActor import LoggingActor
from game.serializers import CustomGameSerializer


class GameActor(ActorTypeDispatcher):
    """
    Define an actor that will play the game based on the state of the game instance pulled from the database.
    """

    def __init__(self):
        """
        Initialize all the attributes required for managing the whole game.
        """

        # Initialize the parent class
        super(GameActor, self).__init__()

        # Declare default UI manager
        self._ui = None
        self._logger = None

        # Game required attributes
        self._game = None
        self._players = {}  # player_code: player_addr
        self._walls = []
        self._empty_tiles = set([(x, y) for x in range(0, MAP_WIDTH) for y in range(0, MAP_HEIGHT)])
        self._available_colors = {'red', 'green', 'blue', 'brown'}
        self._available_heroes = {1, 2, 3, 4}

    def receiveMsg_dict(self, message, sender):
        """
        Define the action to perform upon reception of a message of type dict.
        :param message: A dictionary formatted as follow: {action: ..., data: ..., orig: ... }
        :param sender: The ActorAddress of the sending actor.
        :return: Nothing.
        """

        # Extract all information from the message
        action, data, orig = extract_msg(message)
        # Execute the required action
        if action == 'init':
            # Initialize the logging actor
            self._logger = self.createActor(LoggingActor, globalName=LOGGING_NAME)
            self.send(self._logger, format_msg('debug', data="{} - Init".format(__name__)))
            # Extract the code of the game
            game_code = data.get('code')
            # Check if the object already exist in database
            try:
                self._game = Game.objects.prefetch_related().get(code__exact=game_code)
            except ObjectDoesNotExist:
                # This is a new game, not a recovery from a failure
                self._game = Game()
                # Initialize the code and build the url
                self._game.code = game_code
                self._game.url = "{}/{}/".format(BASE_GAME_URL, game_code)

                # Choose a random board
                map = self._get_board_from_file()
                # Save the board to database
                map.save()
                commit()
                # Add the map to the game
                self._game.map = map

            # Initialize the actor's internal state
            self._add_walls()

            # Randomly place the dragon, mines, markets, items and enemies
            self._add_random_mine()
            self._add_random_markets()
            self._add_random_enemy()
            self._add_random_item()

            # Create THE dragon
            rnd_pos = choice(list(self._empty_tiles))
            self._empty_tiles.remove(rnd_pos)
            self._game.map.enemy.create(pos_x=rnd_pos[0], pos_y=rnd_pos[1], type='dragon', health=DRAGON_HEALTH, strength=DRAGON_STRENGTH)

            # Save the board and game in database
            self._game.map.save()
            self._game.save()

            # Update the string representation of the map
            self._update_board()

            # Save the board and game in database
            self._game.map.save()
            self._game.save()
            commit()

            # Send the code and address back to the parent actor, to add the game to the lookup table
            lookup = self.createActor('game.actors.LookupActor', globalName=LOOKUP_NAME)
            self.send(lookup, format_msg('new', data={'addr': self.myAddress, 'code': game_code}))

            # Send the address back to the original sender (most probably the django view)
            self.send(orig, self.myAddress)
            # Send the game state to the logging actor
            self.send(self._logger, self._game)

        elif action == 'add_player':
            # Extract the user code
            user_code = data.get('code')

            # Check that we have less than four players and the player is not already part of the game
            if self._game.players.all().count() < 4 and self._game.players.all().filter(user__code__exact=user_code).count() < 1:
                try:
                    # Get the user associated with the code
                    user = User.objects.get(code__exact=user_code)
                    # Add a new player associated with the use to the game
                    spawn_pos = choice(list(self._empty_tiles))
                    # Get the id of the corresponding hero
                    try:
                        hero_id = self._available_heroes.pop()
                    except KeyError:
                        # There has been a mistake here
                        self.send(self._logger, format_msg('error', data="{} -- We have ran out of heroes, but are "
                                                                         "still adding players to the game.".format(__name__)))

                        # Terminate the game
                        self._finish(terminate=True)
                        # Send back an error
                        self.send(sender, None)
                        # Terminate the actor
                        self.send(self.myAddress, ActorExitRequest())
                        return

                    # Choose the player's color
                    try:
                        color = self._available_colors.pop()
                    except KeyError:
                        # There has been a mistake here
                        self.send(self._logger, format_msg('error', data="{} -- We have ran out of colors, but are "
                                                                         "still adding players to the game.".format(__name__)))
                        # Terminate the game
                        self._finish(terminate=True)
                        # Send back an error
                        self.send(sender, None)
                        # Terminate the actor
                        self.send(self.myAddress, ActorExitRequest())
                        return
                    player = self._game.players.create(user=user,
                                                       color=color,
                                                       spawn_x=spawn_pos[0],
                                                       spawn_y=spawn_pos[1],
                                                       pos_x=spawn_pos[0],
                                                       pos_y=spawn_pos[1],
                                                       hero_id=hero_id)
                    # Remove the tile from the set of empty tiles
                    try:
                        self._empty_tiles.remove(spawn_pos)
                    except KeyError:
                        # Terminate the game
                        self._finish(terminate=True)
                        # Send back an error
                        self.send(sender, None)
                        # Terminate the actor
                        self.send(self.myAddress, ActorExitRequest())
                        pass

                    # Create a child actor for the player
                    actor_addr = self.createActor(PlayerActor)
                    self.send(actor_addr, format_msg('init', data=player.state))
                    self._players.update({user_code: actor_addr})

                    # Save the player and game in database
                    player.save()
                    self._game.save()
                    commit()

                    if self._game.players.all().count() == 4:
                        # If the game is full send a message both the lookup and supervisor actors
                        lookup = self.createActor('game.actors.LookupActor', globalName=LOOKUP_NAME)
                        supervisor = self.createActor(SupervisorActor, globalName=SUPERVISOR_NAME)
                        self.send(lookup, format_msg('full', data={'code': self._game.code}))
                        self.send(supervisor, format_msg('full', data={'code': self._game.code}))
                        # Update the state of the game from Initializing to Waiting
                        self._game.state = "W"
                        # Save the game
                        self._game.save()
                        commit()

                    # Register the player actor address in the database
                    player_lookup = self.createActor(PlayerLookupActor, globalName=PLAYER_LOOKUP_NAME)
                    self.send(player_lookup, format_msg('save', data={'game_code': self._game.code,
                                                                      'user_code': user_code, 'addr': actor_addr}))

                    # Send player address, game code and serialized game state back to sender
                    serializer = CustomGameSerializer(self._game, context={'your_hero': player})
                    self.send(sender, {'game_state': serializer.data})
                except ObjectDoesNotExist:
                    self.send(self._logger, format_msg('error', data="{} -- Could not find"
                                                                     " user {}.".format(__name__, user_code)))
                    self.send(sender, None)
            else:
                self.send(sender, None)

        elif action == 'play':
            self.send(self._logger, format_msg('debug', data="{} - Play".format(__name__)))
            # Ask to be woken up in a second
            self.wakeupAfter(timePeriod=timedelta(seconds=1))
            # Set the state of the players
            for player in self._game.players.all().iterator():
                player.state = "P"
                player.save()
                # If the player is still part of the game
                if player.user.code in self._players:
                    self.send(self._players[player.user.code], format_msg('update', data=player.state))
            # Set the state of the game
            self._game.state = "P"
            # Save the initial state of the game
            self._game.save()
            commit()

        elif action == "ui":
            # Create child actors
            self._ui = self.createActor(UIManagerActor, globalName=UI_MANAGER_NAME)

        elif action == 'next_action':
            # Make sure the game is still playing
            if self._game.state == "P":
                # Get the player
                player_code = data.get('code')
                if player_code is not None:
                    player = self._game.players.all().get(user__code__exact=player_code)
                    player.action = data.get('action')

                    # Check if the player died since last time
                    if player.state == 'D':
                        # The player is alive again (praised be odin)
                        player.state = 'P'
                    else:
                        # Collect all nearby items
                        self._collect_items(player)

                        # Try to move around
                        if not self._move_around(player):
                            # Buy items if possible
                            if not self._buy_item(player):
                                # Attack a mine
                                if not self._attack_mine(player):
                                    # Fight a nearby enemy
                                    if not self._fight_enemy(player):
                                        # Fight a nearby hero
                                        self._fight_hero(player)
                        # Send game state to UIManager if necessary
                        if self._ui is not None:
                            self.send(self._ui, self._game)

                        # Update the board
                        self._update_board()
                        self._game.map.save()

                    # Save the player
                    player.save()

                    # Save the game
                    self._game.save()
                    commit()

                    # Send serialized game state back to orig
                    serializer = CustomGameSerializer(self._game, context={'your_hero': player})
                    self.send(orig, format_msg('ok', data=serializer.data))

                    # Update the player attribute of the PlayerActor
                    self.send(sender, format_msg('update', data=player.state))

                    # Send the game state to the logging actor
                    self.send(self._logger, self._game)
                else:
                    self.send(orig, format_msg('error', data='Could not find this player in this game.'))
            else:
                self.send(orig, format_msg('error', data='The game has already ended. No more action possible.'))

        elif action == 'finish':
            # Save the scores and update the players, board and game states
            self._finish()
            # Terminate the actor
            self.send(self.myAddress, ActorExitRequest())

        elif action == 'player_addr':
            user_code = data.get('user_code', None)
            # Send the player address associated with the given user code
            self.send(orig, self._players.get(user_code, None))

    def receiveMsg_WakeupMessage(self, message, sender):
        """
        Simply play one turn of the game. Moving enemies and upgrade markets around, and adding more enemies or items.
        :param message: An instance of the WakeupMessage class containing the delayPeriod as attribute.
        :param sender: The ActorSystem itself. Can safely be ignored here.
        :return: Nothing.
        """

        if self._game.state == "P":
            # Increase the number of turns played
            self._game.turn += 1
            self.send(self._logger, format_msg('debug', data="{} - Executing turn {} with {} players.".format(__name__, self._game.turn, len(self._players))))

            # Update players gold from mines
            for player in self._game.players.all().iterator():
                self._update_gold_from_mines(player)
                player.save()

            # Move skeletons around
            self._move_skeletons()

            # Move the upgrade markets around
            self._move_upgrade_market()

            # Add items to the map
            self._add_random_item()

            # Add skeletons to the map
            self._add_random_enemy()

            # Update the board
            self._update_board()

            # Save the game and board
            self._game.map.save()
            self._game.save()
            commit()

            # If the maximum number of turns has been reached, end the game
            if self._game.turn >= MAX_TURN:
                self.send(self.myAddress, format_msg('finish'))

            # Send game state to UIManager if available
            if self._ui is not None:
                self.send(self._ui, self._game)

            # Send the game state to the logging actor
            self.send(self._logger, self._game)

        # Ask to be woken up in a second
        self.wakeupAfter(timePeriod=timedelta(seconds=1))

    def receiveMsg_ChildActorExited(self, message, sender):
        """
        Simply remove the player from the list of connected players.
        :param message: An instance of the ChildActorExited class, containing the childAddress attribute
        :param sender: The ActorAddress of the ActorSystem. Ignore it.
        :return: Nothing.
        """

        # Retrieve the player code
        for player_code in dict(self._players):
            if self._players[player_code] == message.childAddress:
                # Remove the player actor address from the database
                player_lookup = self.createActor(PlayerLookupActor, globalName=PLAYER_LOOKUP_NAME)
                self.send(player_lookup, format_msg('remove', data={'game_code': self._game.code,
                                                                    'user_code': player_code}))

                # Mark the player as terminated
                player = self._game.players.all().get(user__code__exact=player_code)
                self._empty_tiles.add((player.pos_x, player.pos_y))
                player.state = 'T'
                player.pos_x = -1
                player.pos_y = -1
                player.save()
                commit()

                # Remove the player from the lookup table
                try:
                    self._players.pop(player_code)
                except KeyError:
                    self.send(self._logger, format_msg('error', data="{} -- Could not find player"
                                                                     " {} in players {}.".format(__name__,
                                                                                                 player_code,
                                                                                                 self._players)))

                # If the game is still in its initialization state
                if self._game.state == "I":
                    # Make the color available
                    self._available_colors.add(player.color)
                    # Make the hero available
                    self._available_heroes.add(player.hero_id)
                    # Remove the player from the list of players
                    self._game.players.all().filter(user__code__exact=player_code).delete()
                    # Save the game object
                    self._game.save()

                self.send(self._logger, format_msg('debug', data="{} - Player {} exited".format(__name__, player_code)))
                break

        # Send game state to UIManager if available
        if self._ui is not None:
            self.send(self._ui, self._game)

        # Check if the game was playing and there is at least one remaining player
        if len(self._players) <= 0:
            if self._game.state == "P":
                self.send(self.myAddress, format_msg('finish'))
            else:
                # Terminate the game
                self._finish(terminate=True)
                # Terminate the actor
                self.send(self.myAddress, ActorExitRequest())

    def _get_board_from_file(self):
        """
        Choose a random file from all the available configuration and initialize an instance of the Board model.
        :return: Board. The initialized Board instance.
        """

        # Get the name of the configuration file
        filename = choice(BOARD_CONFIG_FILES)

        # Read the file and initialize the Board instance
        with open(filename, "r") as conf_f:
            data = ujson.load(conf_f)
            txt_file = data.get('str_map')
            img_path = data.get('img_path')

        # Get the string representation of the map
        with open(os.path.join(Vikingdoom.settings.BASE_DIR, txt_file), "r") as txt_conf:
            str_map = txt_conf.readline()

        # Return the initialized board instance
        return Board(str_map=str_map, img_path=img_path)

    def _add_walls(self):
        """
        Find where the walls are on the map.
        :return: Nothing.
        """

        # Get a shortcut to the board
        board = self._game.map

        # Traverse the whole string
        idx = 0
        while idx < len(board.str_map):
            # Get the object referenced by the index
            obj = board.str_map[idx:idx+2]
            idx += 1

            # Compute the coordinates
            y = idx // (MAP_WIDTH * 2)
            x = floor((idx % (MAP_WIDTH * 2)) / 2)  # The division by 2 is due to the fact that each tile is represented by two characters

            if obj == "##":
                idx += 1
                # Add coordinates to walls
                self._walls.append((x, y))
                self._empty_tiles.remove((x, y))

    def _collect_items(self, player):
        """
        Collect all the items around a given player if any.
        :param player: An instance of the Player model.
        :return: Nothing.
        """

        # Get all the nearby instances of item
        items = self._get_nearby_items(player.pos_x, player.pos_y)

        # If there are any
        if len(items) != 0:
            # Just collect them and increase the player's stats in consequence
            for item in items:
                if item.type == 'potion':
                    # Increase the player's health
                    player.health = min(player.health + item.value, DEFAULT_PLAYER_HEALTH)
                    player.last_action = 'D'

                    # Remove the object from the database
                    self._remove_item(item)
                else:
                    # Increase the player's gold
                    player.gold += item.value

                    # Remove the object from the database
                    self._remove_item(item)

    def _buy_item(self, player):
        """
        If any market is nearby and the player can afford it, buy an item.
        :param player: An instance of the Player model.
        :return: Boolean. True if something is bought. False otherwise.
        """

        # Check for markets around
        markets = self._get_nearby_markets(player.pos_x, player.pos_y)

        # If any
        if len(markets) != 0 and player.gold >= DEFAULT_MARKET_PRICE:
            # Buy an item wherever possible
            for market in markets:
                if market.type == 'potion_m' and player.health < DEFAULT_PLAYER_HEALTH:
                    player.health = min(POTION_MARKET_VALUE + player.health, DEFAULT_PLAYER_HEALTH)
                    player.gold -= market.price
                    player.last_action = 'D'
                    player.action = 'B'
                    return True

                if market.type == 'upgrade_m' and player.strength < MAX_PLAYER_STRENGTH:
                    player.strength = min(player.strength + 5, MAX_PLAYER_STRENGTH)
                    player.gold -= market.price
                    player.last_action = 'B'
                    player.action = 'B'
                    return True

            # If nothing has been done
            return False

    def _attack_mine(self, player):
        """
        If a nearby mine is not your own, pillage is in order.
        :param player: An instance of the Player model.
        :return: Boolean. True if a mine is attacked. False otherwise
        """

        # If a mine not owned by the player is nearby
        mines = self._get_nearby_mines(player.id, player.pos_x, player.pos_y)
        if len(mines) != 0:
            # Act on the first mine only
            mine = mines[0]
            # Update the guardian
            enemy = mine.guardian
            enemy.action = 'F'
            enemy.health -= player.strength
            if enemy.health <= 0:
                # Increase the player's strength
                player.strength = min(player.strength + 1, MAX_PLAYER_STRENGTH)
                enemy.health = DEFAULT_ENEMY_HEALTH
                mine.owner = player

            # Save the enemy and mine in database
            enemy.save()
            mine.save()
            commit()

            # Update the player
            player.last_action = 'F'
            player.action = 'F'
            self._decrease_health(player, enemy)

            # An action has been performed
            return True
        else:
            # No action here
            return False

    def _fight_enemy(self, player):
        """
        Fight one nearby enemy at random.
        :param player: An instance of the Player model.
        :return: Boolean. True if an action is performed. False otherwise.
        """

        # If enemies are nearby
        enemies = self._get_nearby_enemies(player.pos_x, player.pos_y)  # Careful of the dying dragon !!!
        if len(enemies) != 0:
            # Randomly select an enemy to fight
            enemy = choice(enemies)

            # Update the enemy
            enemy.action = 'F'
            enemy.health -= player.strength
            if enemy.health <= 0:
                # Increase the player's strength
                player.strength = min(player.strength + 1, MAX_PLAYER_STRENGTH)
                enemy.dead = True
                if enemy.type == 'dragon':
                    # Increase the player's gold
                    player.gold += DRAGON_GOLD
                # Remove the enemy from the game
                self._remove_enemy(enemy)
            else:
                # Save the enemy
                enemy.save()
                commit()

            # Update the player
            player.last_action = 'F'
            player.action = 'F'
            self._decrease_health(player, enemy)

            # An action has been performed
            return True
        else:
            # No action done
            return False

    def _fight_hero(self, player):
        """
        Fight another hero that so happens to be close to you.
        :param player: An instance of the Player model.
        :return: Boolean. True if a fight broke in. False otherwise.
        """

        # Check if a hero is within axe's reach
        players = self._get_nearby_players(player)
        if len(players) != 0:
            # Update the first nearby player
            n_player = players[0]
            self._decrease_health(n_player, player)  # In this case the player is the enemy for the nearby player
            # Save the state of the nearby player
            n_player.save()
            commit()

            # Update our current player
            # No life is taken here since the nearby player will
            # most likely attack you in the same turn
            player.last_action = "F"
            player.action = "F"

            # Fight has been fought
            return True
        else:
            # Nothing has been done
            return False

    def _move_around(self, player):
        """
        Take the player's requested action into consideration and move the hero accordingly.
        :param player: An instance of the Player model.
        :return: Boolean. True if move is valid. False otherwise.
        """

        # If no action has been performed we take the user's request into consideration
        action = player.action.upper()

        # Store the player's action as its last action
        player.last_action = action
        player.action = action

        if action in NEIGHBOUR_TILES:
            # Recover the move requested by the user
            move = NEIGHBOUR_TILES[action]

            # Check if the move is valid
            next_pos = player.pos_x + move[0], player.pos_y + move[1]
            if next_pos in self._empty_tiles and next_pos != (player.pos_x, player.pos_y):  # Idle is not considered an action
                # Update the set of empty tiles
                self._empty_tiles.add((player.pos_x, player.pos_y))
                self._empty_tiles.remove(next_pos)
                # Actually move the player
                player.pos_x = next_pos[0]
                player.pos_y = next_pos[1]
                # Move was valid
                return True
            else:
                # Invalid move or idle
                return False
        else:
            # Invalid action
            return False

    def _reset_guardian_action(self):
        """
        Simply reset the action field to its default value of 'I'.
        :return: Nothing.
        """

        for mine in self._game.map.mine.all().iterator():
            # Update the mine guardian
            mine.guardian.action = 'I'

    def _move_skeletons(self):
        """
        Move the skeleton enemies around randomly.
        :return: Nothing.
        """

        for enemy in self._game.map.enemy.all().iterator():
            # Check that it is a skeleton
            if enemy.type == "skeleton" and enemy.action != "F":
                # Get the current position
                curr_pos = enemy.pos_x, enemy.pos_y
                # Pick a random next postion
                next_pos = self._get_random_move(curr_pos[0], curr_pos[1])
                # Update the set of empty tiles
                self._empty_tiles.add(curr_pos)
                self._empty_tiles.remove(next_pos)
                # Update the enemy's position
                enemy.pos_x = next_pos[0]
                enemy.pos_y = next_pos[1]
            else:
                enemy.action = 'I'

            # Save the state of the enemy
            enemy.save()
            commit()

    def _move_upgrade_market(self):
        """
        Move the upgrade market to a new random position.
        :return: Nothing.
        """

        for market in self._game.map.market.all().iterator():
            # Check the type
            if market.type == "upgrade_m":
                # Move the market
                curr_pos = market.pos_x, market.pos_y
                next_pos = self._get_random_move(curr_pos[0], curr_pos[1])
                market.pos_x = next_pos[0]
                market.pos_y = next_pos[1]
                # Update the set of empty tiles
                self._empty_tiles.add(curr_pos)
                self._empty_tiles.remove(next_pos)

                # Save the market in database
                market.save()
                commit()

    def _decrease_health(self, player, enemy):
        """
        Decrease the life of a given player when in a fight against a given enemy.
        :param player: An instance of the Player model
        :param enemy: An instance of the Enemy model
        :return: Nothing.
        """

        # Decrease the player's life
        player.health -= enemy.strength

        # Check if the player died
        if player.health <= 0:
            # Get the player his full life back
            player.health = DEFAULT_PLAYER_HEALTH
            # Disown the player from all his mines
            for mine in self._game.map.mine.all().filter(owner__exact=player).iterator():
                mine.owner = None
                mine.save()
                commit()

            # Respawn the player in his initial position
            self._empty_tiles.add((player.pos_x, player.pos_y))
            player.pos_x = player.spawn_x
            player.pos_y = player.spawn_y
            try:
                self._empty_tiles.remove((player.spawn_x, player.spawn_y))
            except KeyError:
                pass

            # Set the player's state to Dead
            player.state = 'D'

    def _update_gold_from_mines(self, player):
        """
        Update the player's level of gold depending on the mines owned.
        :param player: The player object.
        :return: Nothing.
        """

        # Increase the player's gold level according to each mine's gold_rate
        for mine in self._game.map.mine.all().filter(owner__exact=player).iterator():
            player.gold += mine.gold_rate

    def _get_nearby_items(self, pos_x, pos_y):
        """
        Check if there are any items near the player's current position.
        :param pos_x: The player's current position along the X axis.
        :param pos_y: The player's current position along the Y axis.
        :return: List. A list of all item objects near the player's current position.
        """

        # Initialize the list of items
        items = []

        # If any item is close to the player it is added to the list
        for item in self._game.map.item.all().iterator():
            if (item.pos_x - pos_x, item.pos_y - pos_y) in NEIGHBOUR_TILES.values():
                items.append(item)

        # Return the list of items
        return items

    def _get_nearby_markets(self, pos_x, pos_y):
        """
        Check if the player is nearby any market.
        :param pos_x: The player's current position along the X axis.
        :param pos_y: The player's current position along the Y axis.
        :return: List. Return a list of all the market objects near the player's current position.
        """

        # Initialize the market list
        markets = []

        # If any market is less than a square away from the player it is added to the list
        for market in self._game.map.market.all().iterator():
            m_x, m_y = market.pos_x, market.pos_y
            if (m_x - pos_x, m_y - pos_y) in NEIGHBOUR_TILES.values():
                markets.append(market)

        # Return the list of objects
        return markets

    def _get_nearby_mines(self, player_id, pos_x, pos_y):
        """
        Check if there is any mine near the player that do not belong to the player.
        :param player_id: The identification number of the player, queried from the database.
        :param pos_x: The player's position along the X axis.
        :param pos_y: The player's position along the Y axis.
        :return: List. Return a list of all the mine objects near the player's current position and that do not belong
        to the player.
        """

        # Initialize the mine list
        mines = []

        # If any mine is less than a square away from the player it is loaded from the database to check for ownership
        for mine in self._game.map.mine.all().iterator():
            if (mine.pos_x - pos_x, mine.pos_y - pos_y) in NEIGHBOUR_TILES.values():
                if mine.owner is None or mine.owner.id != player_id:
                    mines.append(mine)

        # Return the list of mines
        return mines

    def _get_nearby_enemies(self, pos_x, pos_y):
        """
        Check if there are any enemies near the player current position.
        :param pos_x: The player's current position along the X axis.
        :param pos_y: The player's current position along the Y axis.
        :return: List. A list of all the enemy surrounding the player.
        """

        # Initialize a list of enemies
        enemies = []

        # If any enemy is less than one square away from the player it is added to the list
        for enemy in self._game.map.enemy.all().filter(type__in=['skeleton', 'dragon']).iterator():
            if (enemy.pos_x - pos_x, enemy.pos_y - pos_y) in NEIGHBOUR_TILES.values():
                    enemies.append(enemy)

        # Return the enemies list
        return enemies

    def _get_nearby_players(self, player):
        """
        Check if there is any player near the current player's position.
        :param player: The current player.
        :return: List. A list of all nearby players if any. An empty list otherwise.
        """

        # Get all nearby players if any
        nearby_players = []
        for p in self._game.players.all().iterator():
            if p.id != player.id and (p.pos_x - player.pos_x, p.pos_y - player.pos_y) in NEIGHBOUR_TILES.values():
                nearby_players.append(p)

        # Return the list of nearby players
        return nearby_players

    def _add_random_item(self):
        """
        Add new items on the map to maintain the population number.
        :return: Nothing.
        """

        # Get all item types
        types = ['potion', 'gold', 'big_gold']

        while self._game.map.item.all().count() < MAX_ITEMS:
            # Choose a position
            itm_pos = choice(list(self._empty_tiles))
            self._empty_tiles.remove(itm_pos)
            # Choose a type
            itm_type = choice(types)
            # Create a new item in the database
            if itm_type == "big_gold":
                itm_value = DEFAULT_ITEM_VALUE * 2
            else:
                itm_value = DEFAULT_ITEM_VALUE
            self._game.map.item.create(pos_x=itm_pos[0], pos_y=itm_pos[1], type=itm_type, value=itm_value)

    def _add_random_enemy(self):
        """
        Add enemies on the map to maintain the population number.
        :return: Nothing.
        """

        while self._game.map.enemy.all().filter(type__exact="skeleton").count() < MAX_ENEMIES:
            # Choose a position
            enemy_pos = choice(list(self._empty_tiles))
            self._empty_tiles.remove(enemy_pos)
            # Create a new enemy in the database
            self._game.map.enemy.create(pos_x=enemy_pos[0], pos_y=enemy_pos[1], type="skeleton")

    def _add_random_mine(self):
        """
        Add a random number of mines on the map at random locations.
        :return: Nothing
        """

        # How many mines do we want
        nb_mines = randint(*RANGE_MINE)

        # Create mine and guardian at a random location
        cpt = 0
        while cpt < nb_mines:
            cpt += 1
            # Choose a position
            rnd_pos = choice(list(self._empty_tiles))
            self._empty_tiles.remove(rnd_pos)
            # Create an enemy to protect the mine
            enemy = self._game.map.enemy.create(pos_x=rnd_pos[0], pos_y=rnd_pos[1], type='orc', protected=True)
            commit()
            # Create a mine
            self._game.map.mine.create(pos_x=rnd_pos[0], pos_y=rnd_pos[1], guardian=enemy)
            commit()

    def _add_random_markets(self):
        """
        Add a random number of upgrade and potion markets to the map at random locations.
        :return: Nothing.
        """

        # How many upgrade markets
        nb_mkt = randint(*RANGE_MARKET_U)

        # Create the upgrade markets
        cpt = 0
        while cpt < nb_mkt:
            cpt += 1

            # Choose a position
            rnd_pos = choice(list(self._empty_tiles))
            self._empty_tiles.remove(rnd_pos)
            # Create a market
            self._game.map.market.create(pos_x=rnd_pos[0], pos_y=rnd_pos[1], type='upgrade_m')
            commit()

        # How many potion markets
        nb_mkt = randint(*RANGE_MARKET_P)
        cpt = 0
        while cpt < nb_mkt:
            cpt += 1

            # Choose a position
            rnd_pos = choice(list(self._empty_tiles))
            self._empty_tiles.remove(rnd_pos)
            # Create a market
            self._game.map.market.create(pos_x=rnd_pos[0], pos_y=rnd_pos[1], type='potion_m')
            commit()

    def _update_board(self):
        """
        Update the string representation of the board.
        :return:
        """

        # Initialize the representation
        lst_map = [" " for _ in range(0, 2 * MAP_WIDTH * MAP_HEIGHT)]

        # Mark the position of the enemies
        for enemy in self._game.map.enemy.all().iterator():
            # Translate the coordinates to the flat list
            pos = enemy.pos_x * 2 + enemy.pos_y * (MAP_WIDTH * 2)
            # Mark the position in the list
            lst_map[pos] = "!"
            lst_map[pos+1] = enemy.type[0].upper()

        # Mark the position of the items
        for item in self._game.map.item.all().iterator():
            # Translate the position to the flat list
            pos = item.pos_x * 2 + item.pos_y * (MAP_WIDTH * 2)
            # Mark the position in the list
            lst_map[pos] = "?"
            lst_map[pos+1] = item.type[0].upper()

        # Mark the position of the markets
        for market in self._game.map.market.all().iterator():
            # Translate the position
            pos = market.pos_x * 2 + market.pos_y * (MAP_WIDTH * 2)
            # Mark the market on the map
            lst_map[pos] = "~"
            lst_map[pos+1] = market.type[0].upper()

        # Mark the position of the mines
        for mine in self._game.map.mine.all().iterator():
            # Translate the position for the flat list
            pos = mine.pos_x * 2 + mine.pos_y * (MAP_WIDTH * 2)
            # Mark the mine on the map
            lst_map[pos] = "$"
            # Check for owner chip
            if mine.owner is not None:
                lst_map[pos+1] = str(mine.owner.hero_id)
            else:
                lst_map[pos+1] = "_"

        # Mark the position of the Heroes
        for player in self._game.players.all().iterator():
            # Translate the position for the flat list
            pos = player.pos_x * 2 + player.pos_y * (MAP_WIDTH * 2)
            # Mark the player on the map
            lst_map[pos] = "@"
            lst_map[pos+1] = str(player.hero_id)

        # Mark the walls
        for pos_w in self._walls:
            # Translate the position for the flat list
            pos = pos_w[0] * 2 + pos_w[1] * (MAP_WIDTH * 2)
            # Mark the wall on the map
            lst_map[pos] = "#"
            lst_map[pos+1] = "#"

        # Update the string representation of the map
        self._game.map.str_map = "".join(lst_map)

    def _get_random_move(self, pos_x, pos_y):
        """
        Choose a random move among the possible moves, that do not end up in a wall or other item.
        :param pos_x: The current position of the character along the X axis.
        :param pos_y: The current position of the character along the Y axis.
        :return: Tuple. The new position of the character along the X and Y axis respectively.
        """

        # Initialize the next move
        available_moves = set(NEIGHBOUR_TILES.values())
        tried_moves = set()

        while len(available_moves.difference(tried_moves)) > 0:
            # Take another shot at glory
            move = choice(list(available_moves.difference(tried_moves)))
            next_pos = pos_x + move[0], pos_y + move[1]
            tried_moves.add(next_pos)
            if next_pos in self._empty_tiles or next_pos == (pos_x, pos_y):
                return next_pos

        # Return the next position
        return pos_x, pos_y

    def _remove_enemy(self, enemy):
        """
        Delete an enemy instance from the board, the enemies dict and finally from the database.
        :param enemy: The enemy instance to remove.
        :return: Nothing.
        """

        # Make sure the enemy is not protected (mine guardian)
        if not enemy.protected:
            # Remove the enemy from the map
            self._game.map.enemy.remove(enemy)
            # Free its tile
            self._empty_tiles.add((enemy.pos_x, enemy.pos_y))

    def _remove_item(self, item):
        """
        Delete an item instance from the board, the items dict and finally from the database.
        :param item: The item instance to remove.
        :return: Nothing.
        """

        # Remove the item from the map
        self._game.map.item.remove(item)
        # Free its tile
        self._empty_tiles.add((item.pos_x, item.pos_y))

    def _remove_mine(self, mine):
        """
        Delete an mine instance from the board, the mines dict and finally from the database.
        :param mine: The mine instance to remove.
        :return: Nothing.
        """

        # Remove the mine and its guardian from the map
        self._game.map.enemy.remove(mine.guardian)
        self._game.map.mine.remove(mine)
        # Free its tile
        self._empty_tiles.add((mine.pos_x, mine.pos_y))

    def _remove_market(self, market):
        """
        Delete an market instance from the board, the markets dict and finally from the database.
        :param market: The market instance to remove.
        :return: Nothing.
        """

        # Remove the market from the map
        self._game.map.market.remove(market)
        # Free its tile
        self._empty_tiles.add((market.pos_x, market.pos_y))

    def _finish(self, terminate=False):
        """
        Reset the state of the players and record the players' score.
        This function is called at the end of each game in the main loop.
        :param terminate: Boolean value indicating if the game is being terminated or gracefully exiting.
        :return: Nothing.
        """

        if self._game is not None:
            # Update the game's state
            self._game.state = "F"

            # Get the player lookup actor address
            player_lookup = self.createActor(PlayerLookupActor, globalName=PLAYER_LOOKUP_NAME)

            # For each player
            for player in self._game.players.all().iterator():
                if not terminate:
                    # Record the score
                    score = Score(game=self._game, user=player.user, score=player.gold)
                    score.save()
                    commit()

                # State
                player.state = "T"
                player.action = ''
                # Update the database object
                if self._players.get(player.user.code, None) is not None:
                    self.send(self._players.get(player.user.code), format_msg('update', data=player.state))
                # Save the player in database
                player.save()
                commit()

                # Remove the player actor address from the database
                self.send(player_lookup, format_msg('remove', data={'game_code': self._game.code,
                                                                    'user_code': player.user.code}))

            # Remove enemies, items, mines and markets from the board
            for mine in self._game.map.mine.all().iterator():
                self._remove_mine(mine)

            for enemy in self._game.map.enemy.all().iterator():
                self._remove_enemy(enemy)

            for item in self._game.map.item.all().iterator():
                self._remove_item(item)

            for market in self._game.map.market.all().iterator():
                self._remove_market(market)

            # Update the state of the game
            self._game.map.save()
            self._game.save()
            commit()

            # Send game state to UIManager if necessary
            if self._ui is not None:
                self.send(self._ui, self._game)

            # Send the game state to the logging actor
            self.send(self._logger, self._game)
