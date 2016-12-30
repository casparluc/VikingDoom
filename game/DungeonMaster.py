#!/usr/bin/python
# -*- coding: utf-8 -*-
from .models import *
from time import sleep
import logging
from random import choice
from math import floor
from django.db.transaction import commit

# Global variables
NEIGHBOUR_TILES = {'E': (1, 0), 'S': (0, 1), 'W': (-1, 0), 'N': (0, -1), 'I': (0, 0)}
MAX_TURN = 1000
POTION_MARKET_VALUE = 10
MAX_PLAYER_STRENGTH = 25
DRAGON_GOLD = 500
DRAGON_STRENGTH = DEFAULT_PLAYER_HEALTH / 4
DRAGON_HEALTH = 10000
ORC_STRENGTH = 5
MAX_ENEMIES = 10
MAX_ITEMS = 10
MAX_TRIALS = 3


class DungeonMaster:
    """
    The Dungeon Master consumes games that are Waiting in the queue (the database).
     After initializing the games attributes and its own internal variables, the Dungeon Master handles every aspects of
     the game from health points to moving players/enemies around, to spawning items and so on.
     At the end of the game, the Dungeon Master records the score of each player, tags the game as finished and reset
     the player's attribute before moving on to the next game.
    """

    def __init__(self):
        # Initialize all the attributes necessary to managing the game
        self._game = None
        self._items = {}  # id: (x,y)
        self._enemies = {}  # id: (x,y)
        self._players = []
        self._walls = []
        self._empty_tiles = set([(x, y) for x in range(0, MAP_WIDTH) for y in range(0, MAP_HEIGHT)])
        self._mines = {}  # id: (x,y)
        self._markets = {}  # id: (x,y)
        self._logger = logging.getLogger("Game.DungeonMaster")
        self._trials = {}
        self._times = {}

    def _initialize(self):
        """
        Initialize the game, the players and any internal value. Create the board to be used.
        This function is called at the beginning of each loop in the main function.
        :return: Boolean. False if no game can be found in the queue. True Otherwise.
        """

        # Get the next waiting game
        try:
            self._game = Game.objects.order_by('modified').filter(state__exact="W").first()
        except IndexError as e:
            self._logger.exception(e)
            return False

        if self._game is not None:
            # Update the game status
            self._logger.info("Now playing game: {}".format(self._game.id))
            self._game.state = "P"

            # Record the participating players
            self._players = [self._game.player_1, self._game.player_2, self._game.player_3, self._game.player_4]

            # Get the board from a random configuration file
            self._init_board_from_str()

            # Initialize the players' spawn locations
            colors = ['red', 'green', 'blue', 'brown']
            for player, color in zip(self._players, colors):
                # Choose a location on the map that is not taken
                spawn_pos = choice(list(self._empty_tiles))
                self._empty_tiles.remove(spawn_pos)
                # Update the players spawn position and initial position
                player.pos_x = spawn_pos[0]
                player.pos_y = spawn_pos[1]
                player.spawn_x = spawn_pos[0]
                player.spawn_y = spawn_pos[1]
                # Change the player's color
                player.color = color
                # Save the changes in the database
                player.save()
                commit()

                # Update the number of trials for the player
                self._trials.update({player.id: 0})

            # Update the game in database
            self._game.save()
            commit()

            # Yeah we found a game
            return True
        else:
            # This is not the game you are looking for
            return False

    def _init_board_from_str(self):
        """
        Fill in the missing configuration for the board from its string representation.
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

            if obj[0] == "$":
                idx += 1
                # Create an enemy to protect the mine
                enemy = Enemy(pos_x=x, pos_y=y, type='orc', protected=True)
                enemy.save()
                commit()
                # Add the enemy to the board
                board.enemy.add(enemy)
                # Create a mine
                mine = Mine(pos_x=x, pos_y=y, guardian=enemy)
                mine.save()
                commit()
                # Add coordinates to the dict
                self._mines.update({mine.id: (x, y)})
                self._empty_tiles.remove((x, y))
                # Add the mine to the board
                board.mine.add(mine)
            elif obj[0] == "#" and obj[1] == "#":
                idx += 1
                # Add coordinates to walls
                self._walls.append((x, y))
                self._empty_tiles.remove((x, y))
            elif obj[0] == "!":
                idx += 1
                if obj[1] == "S":
                    e_type = 'skeleton'
                    health = DEFAULT_ENEMY_HEALTH
                    strength = 1
                elif obj[1] == "O":
                    e_type = 'orc'
                    health = DEFAULT_ENEMY_HEALTH
                    strength = ORC_STRENGTH
                else:
                    e_type = 'dragon'
                    health = DRAGON_HEALTH
                    strength = DRAGON_STRENGTH
                # Create an enemy to protect the mine
                enemy = Enemy(pos_x=x, pos_y=y, type=e_type, health=health, strength=strength)
                enemy.save()
                commit()
                # Add the enemy to the dict
                self._enemies.update({enemy.id: (x, y)})
                self._empty_tiles.remove((x, y))
                # Add the enemy to the board
                board.enemy.add(enemy)
            elif obj[0] == "?":
                idx += 1
                if obj[1] == "P":
                    i_type = 'potion'
                    value = DEFAULT_ITEM_VALUE
                elif obj[1] == "B":
                    i_type = 'big_gold'
                    value = 2 * DEFAULT_ITEM_VALUE
                else:
                    i_type = 'gold'
                    value = DEFAULT_ITEM_VALUE
                # Create item
                item = Item(pos_x=x, pos_y=y, type=i_type, value=value)
                item.save()
                commit()
                # Add coordinates to the dict
                self._items.update({item.id: (x, y)})
                self._empty_tiles.remove((x, y))
                # Add the item to the board
                board.item.add(item)
            elif obj[0] == "~":
                idx += 1
                if obj[1] == "P":
                    m_type = 'potion_m'
                else:
                    m_type = 'upgrade_m'
                # Create a market
                market = Market(pos_x=x, pos_y=y, type=m_type)
                market.save()
                commit()
                # Add the coordinates to the dict
                self._markets.update({market.id: (x, y)})
                self._empty_tiles.remove((x, y))
                # Add the market to the board
                board.market.add(market)

        # Save the board
        board.save()
        commit()

    def _play(self):
        """
        Manages an entire game, from moving the players/enemies around to spawning items.
        This function is always called after initialization in the main loop.
        It is imperative that the main loop of this function is executed with a frequency of 2Hz (every 500ms). To
        allow the players to send an action to the database.
        :return: Nothing.
        """

        # Update the players' state
        for idx, player in enumerate(self._players):
            player.refresh_from_db()
            player.state = "P"
            player.save()
            commit()
            self._times.update({player.id: player.last_answer_time})

        # Refresh the game from the database
        self._game.refresh_from_db()

        while self._game.turn < MAX_TURN and self._is_someone_playing():
            # Increase the turn meter
            self._game.turn += 1
            # Save the number of turns in database
            self._game.save(update_fields=['turn', 'modified', 'state'])
            commit()

            self._logger.info("Turn: {}".format(self._game.turn))
            # For each player
            for player in self._players:
                # Log the state of the player
                self._logger.debug("{} -> T: {}".format(player, self._trials[player.id]))

                # Update the player's level of gold based on mine ownership
                self._update_gold_from_mines(player)
                # Let only non-terminated players play the game
                if player.state in ["P", "D"] and self._wait_for_action(player):
                    if self._wait_for_action(player):
                        acted = False
                        # If there are any items nearby
                        self._collect_items(player)

                        # Buy items if possible
                        if self._buy_item(player):
                            acted = True
                        else:
                            # Attack nearby mines
                            if self._attack_mine(player):
                                acted = True
                            else:
                                # Fight random enemy
                                if self._fight_enemy(player):
                                    acted = True
                                else:
                                    # Fight heroes lying around
                                    if self._fight_hero(player):
                                        acted = True
                                    else:
                                        # If all else fail, just move around
                                        if self._move_around(player):
                                            acted = True
                                        else:
                                            # Invalid move means one less trial
                                            self._increase_trials(player)

                        # If the player was able to act
                        if acted:
                            # Reset the number of trial errors
                            self._reset_trials(player)
                    else:
                        self._logger.info("The player {} did not answer in less than a second.".format(player.id))
                        self._increase_trials(player)
                else:
                    self._logger.info("Ignoring player {}: Terminated".format(player.id))

                # At the end of his turn save the player in the database
                player.action = ''
                player.save()
                commit()
                player.refresh_from_db(fields=['last_answer_time'])
                self._times.update({player.id: player.last_answer_time})

                # Refresh the player from the database
                player.refresh_from_db(fields=['action', 'last_answer_time'])

            # Move the skeleton enemies around randomly
            self._move_skeletons()

            # Update enemies' action
            self._reset_guardian_action()

            # Move any upgrade market around
            self._move_upgrade_market()

            # Update the board before the next turn
            self._add_random_item()
            self._add_random_enemy()
            self._update_board()

            # Save the map in the database
            self._game.map.save()
            commit()

        # Save the whole game in database
        self._game.save()
        commit()
        self._logger.info("The game {} is now finished.".format(self._game.id))
        self._logger.info("---------------------------------------------------------------------------------------------------------------------------------------------------------------")

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
                    if player.health < DEFAULT_PLAYER_HEALTH:
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
        if len(markets) != 0 and player.gold > DEFAULT_MARKET_PRICE:
            # Buy an item wherever possible
            for market in markets:
                if market.type == 'potion_m' and player.health < DEFAULT_PLAYER_HEALTH:
                    player.health = min(POTION_MARKET_VALUE + player.health, DEFAULT_PLAYER_HEALTH)
                    player.gold -= market.price
                    player.last_action = 'D'
                    return True

                if market.type == 'upgrade_m' and player.strength < MAX_PLAYER_STRENGTH:
                    player.strength = min(player.strength + 5, MAX_PLAYER_STRENGTH)
                    player.gold -= market.price
                    player.last_action = 'B'
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

            # Save the mine and enemy in database
            mine.save()
            enemy.save()
            commit()

            # Update the player
            player.last_action = 'F'
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
                # Update the enemy in database
                enemy.save()
                commit()

            # Update the player
            player.last_action = 'F'
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

            # Update our current player
            # No life is taken here since the nearby player will
            # most likely attack you in the same turn
            player.last_action = "F"

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

        if action in NEIGHBOUR_TILES:
            # Recover the move requested by the user
            move = NEIGHBOUR_TILES[action]

            # Check if the move is valid
            next_pos = player.pos_x + move[0], player.pos_y + move[1]
            if next_pos in self._empty_tiles or next_pos == (player.pos_x,
                                                             player.pos_y):
                # Update the set of empty tiles
                self._empty_tiles.add((player.pos_x, player.pos_y))
                self._empty_tiles.remove(next_pos)
                # Actually move the player
                player.pos_x = next_pos[0]
                player.pos_y = next_pos[1]
                # Move was valid
                return True
            else:
                # Write a message to the logs
                self._logger.info("Invalid move increasing trial of player: {}".format(player.id))
                # Invalid move
                return False
        else:
            # Write a message to the logs
            self._logger.info("Invalid action increasing trial of player: {}".format(player.id))
            # Invalid move
            return False

    def _reset_guardian_action(self):
        """
        Simply reset the action field to its default value of 'I'.
        :return: Nothing.
        """

        for m_id in self._mines:
            # Get the mine object
            try:
                mine = Mine.objects.get(pk=m_id)
            except models.ObjectDoesNotExist as e:
                self._logger.exception(e)
                continue

            # Update the mine guardian
            mine.guardian.action = 'I'
            mine.guardian.save(update_fields=['action'])
            commit()

    def _move_skeletons(self):
        """
        Move the skeleton enemies around randomly.
        :return: Nothing.
        """

        for s_id in self._enemies:
            # Get the enemy object
            enemy = Enemy.objects.get(pk=s_id)
            # Check that it is a skeleton
            if enemy.type == "skeleton" and enemy.action != "F":
                # Get the current position
                curr_pos = self._enemies[s_id]
                # Pick a random next postion
                next_pos = self._get_random_move(curr_pos[0], curr_pos[1])
                # Update the set of empty tiles
                self._empty_tiles.add(curr_pos)
                self._empty_tiles.remove(next_pos)
                # Update the enemy's position
                enemy.pos_x = next_pos[0]
                enemy.pos_y = next_pos[1]
                self._enemies[s_id] = next_pos
            else:
                enemy.action = 'I'

            # Save in database
            enemy.save(update_fields=['pos_x', 'pos_y', 'action'])
            commit()

    def _move_upgrade_market(self):
        """
        Move the upgrade market to a new random position.
        :return: Nothing.
        """

        for m_id in self._markets:
            # Get the market object
            market = Market.objects.get(pk=m_id)
            # Check the type
            if market.type == "upgrade_m":
                # Move the market
                curr_pos = self._markets[m_id]
                next_pos = self._get_random_move(curr_pos[0], curr_pos[1])
                market.pos_x = next_pos[0]
                market.pos_y = next_pos[1]
                market.save()
                commit()
                # Update the set of empty tiles
                self._empty_tiles.add(curr_pos)
                self._empty_tiles.remove(next_pos)
                # Update the list of markets' position
                self._markets[m_id] = next_pos

    def _is_someone_playing(self):
        """
        Check that at list one player in the list is still playing the game.
        :return: Boolean. True is one player at least is playing the game. False otherwise.
        """

        # Check for playing player
        for player in self._players:
            if player.state in ['P', 'D']:
                return True
        return False

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
            mines = Mine.objects.filter(owner__exact=player)
            for mine in mines.iterator():
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
                self._logger.exception("Error while respawning player {}: The tile ({}, {}) was not empty.".format(player.id, player.spawn_x, player.spawn_y))
                pass

    def _increase_trials(self, player):
        """
        Increase the number of trials for a given user and set the terminated state if necessary.
        :param player: An instance of the Player model.
        :return: Nothing.
        """

        # Increase the number of trials for the player
        self._trials[player.id] += 1
        # Check if the player has reached the max number of allowed trials.
        if self._trials[player.id] > MAX_TRIALS:
            # Update the player's state
            player.state = "T"
            # Remove the player from the map
            self._empty_tiles.add((player.pos_x, player.pos_y))
            player.pos_x = -1
            player.pos_y = -1

    def _reset_trials(self, player):
        """
        Reset the number of trials for a given user.
        :param player: An instance of the Player model.
        :return: Nothing.
        """

        # Simply but the trial meter back to 0
        self._trials[player.id] = 0

    def _wait_for_action(self, player):
        """
        Wait 1 second for an answer from the player.
        :param player: The player instance.
        :return: Boolean. True if the player has sent a request. False otherwise.
        """

        # Simply wait for that time to pass
        cpt = 0
        while self._times[player.id] == player.last_answer_time and cpt < 10:
            cpt += 1
            sleep(0.2)
            player.refresh_from_db(fields=['action', 'last_answer_time'])

        # Return a boolean representing a change in modification time
        return self._times[player.id] != player.last_answer_time

    def _update_gold_from_mines(self, player):
        """
        Update the player's level of gold depending on the mines owned.
        :param player: The player object.
        :return: Nothing.
        """

        # Increase the player's gold level according to each mine's gold_rate
        for mine in Mine.objects.filter(owner__exact=player):
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
        for i_id in dict(self._items):
            i_x, i_y = self._items[i_id]
            if (i_x - pos_x, i_y - pos_y) in NEIGHBOUR_TILES.values():
                try:
                    items.append(Item.objects.get(pk=i_id))
                except models.ObjectDoesNotExist as e:
                    self._logger.exception(e)
                    self._items.pop(i_id)

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
        for m_id in dict(self._markets):
            m_x, m_y = self._markets[m_id]
            if (m_x - pos_x, m_y - pos_y) in NEIGHBOUR_TILES.values():
                try:
                    markets.append(Market.objects.get(pk=m_id))
                except models.ObjectDoesNotExist as e:
                    self._logger.exception(e)
                    self._markets.pop(m_id)

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
        for m_id in dict(self._mines):
            m_x, m_y = self._mines[m_id]
            if (m_x - pos_x, m_y - pos_y) in NEIGHBOUR_TILES.values():
                try:
                    mine = Mine.objects.get(pk=m_id)
                    if mine.owner is None or mine.owner.id != player_id:
                        mines.append(mine)
                except models.ObjectDoesNotExist as e:
                    self._logger.exception(e)
                    self._mines.pop(m_id)

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
        for e_id in dict(self._enemies):
            e_x, e_y = self._enemies[e_id]
            if (e_x - pos_x, e_y - pos_y) in NEIGHBOUR_TILES.values():
                try:
                    enemies.append(Enemy.objects.exclude(type__exact="orc").get(pk=e_id))
                except models.ObjectDoesNotExist as e:
                    self._logger.exception(e)
                    self._enemies.pop(e_id)

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
        for p in self._players:
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

        while len(self._items) < MAX_ITEMS:
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
            item = Item(pos_x=itm_pos[0], pos_y=itm_pos[1], type=itm_type, value=itm_value)
            item.save()
            commit()
            # Add the item to the map
            self._game.map.item.add(item)
            self._game.map.save()
            commit()
            # Add the item to the list of already present items
            self._items.update({item.id: itm_pos})

    def _add_random_enemy(self):
        """
        Add enemies on the map to maintain the population number.
        :return: Nothing.
        """

        while len(self._enemies) < MAX_ENEMIES:
            # Choose a position
            enemy_pos = choice(list(self._empty_tiles))
            self._empty_tiles.remove(enemy_pos)
            # Create a new enemy in the database
            enemy = Enemy(pos_x=enemy_pos[0], pos_y=enemy_pos[1], type="skeleton")
            enemy.save()
            commit()
            # Add the enemy to the list
            self._game.map.enemy.add(enemy)
            self._game.map.save()
            commit()
            # Add the enemy to the list
            self._enemies.update({enemy.id: enemy_pos})

    def _update_board(self):
        """
        Update the string representation of the board.
        :return:
        """

        # Initialize the representation
        lst_map = [" " for _ in range(0, 2 * MAP_WIDTH * MAP_HEIGHT)]

        # Mark the position of the enemies
        for e_id in self._enemies:
            # Query for the enemy
            try:
                enemy = Enemy.objects.get(pk=e_id)
            except models.ObjectDoesNotExist as e:
                self._logger.exception(e)
                continue

            # Translate the coordinates to the flat list
            pos = enemy.pos_x * 2 + enemy.pos_y * (MAP_WIDTH * 2)
            # Mark the position in the list
            lst_map[pos] = "!"
            lst_map[pos+1] = enemy.type[0].upper()

        # Mark the position of the items
        for i_id in self._items:
            # Query for the item
            try:
                item = Item.objects.get(pk=i_id)
            except models.ObjectDoesNotExist as e:
                self._logger.exception(e)
                continue

            # Translate the position to the flat list
            pos = item.pos_x * 2 + item.pos_y * (MAP_WIDTH * 2)
            # Mark the position in the list
            lst_map[pos] = "?"
            lst_map[pos+1] = item.type[0].upper()

        # Mark the position of the markets
        for m_id in self._markets:
            # Get the market from the database
            try:
                market = Market.objects.get(pk=m_id)
            except models.ObjectDoesNotExist as e:
                self._logger.exception(e)
                continue
            # Translate the position
            pos = market.pos_x * 2 + market.pos_y * (MAP_WIDTH * 2)
            # Mark the market on the map
            lst_map[pos] = "~"
            lst_map[pos+1] = market.type[0].upper()

        # Mark the position of the mines
        for m_id in self._mines:
            # Query the mine object from the database
            try:
                mine = Mine.objects.get(pk=m_id)
            except models.ObjectDoesNotExist as e:
                self._logger.exception(e)
                continue
            # Translate the position for the flat list
            pos = mine.pos_x * 2 + mine.pos_y * (MAP_WIDTH * 2)
            # Mark the mine on the map
            lst_map[pos] = "$"
            # Check for owner chip
            if mine.owner is not None:
                lst_map[pos+1] = str(mine.owner.id)
            else:
                lst_map[pos+1] = "_"

        # Mark the position of the Heroes
        for player in self._players:
            # Translate the position for the flat list
            pos = player.pos_x * 2 + player.pos_y * (MAP_WIDTH * 2)
            # Mark the player on the map
            lst_map[pos] = "@"
            lst_map[pos+1] = str(player.id)

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

        # Remove the enemy from the map
        self._game.map.enemy.remove(enemy)
        self._game.map.save()
        commit()
        # Remove the enemy from the dictionary
        pos = self._enemies.pop(enemy.id)
        # Free its tile
        self._empty_tiles.add(pos)
        # Remove the instance from the database
        enemy.delete()

    def _remove_item(self, item):
        """
        Delete an item instance from the board, the items dict and finally from the database.
        :param item: The item instance to remove.
        :return: Nothing.
        """

        # Remove the item from the map
        self._game.map.item.remove(item)
        self._game.map.save()
        commit()
        # Remove the item from the dictionary
        pos = self._items.pop(item.id)
        # Free its tile
        self._empty_tiles.add(pos)
        # Delete the instance from the database
        item.delete()

    def _remove_mine(self, mine):
        """
        Delete an mine instance from the board, the mines dict and finally from the database.
        :param mine: The mine instance to remove.
        :return: Nothing.
        """

        # Remove the mine and its guardian from the map
        self._game.map.enemy.remove(mine.guardian)
        self._game.map.mine.remove(mine)
        self._game.map.save()
        commit()
        # Remove the mine from the dictionary
        pos = self._mines.pop(mine.id)
        # Free its tile
        self._empty_tiles.add(pos)
        # Delete the instances from the database
        guardian = mine.guardian
        mine.delete()
        guardian.delete()

    def _remove_market(self, market):
        """
        Delete an market instance from the board, the markets dict and finally from the database.
        :param market: The market instance to remove.
        :return: Nothing.
        """

        # Remove the market from the map
        self._game.map.market.remove(market)
        self._game.map.save()
        commit()
        # Remove the market from the dictionary
        pos = self._markets.pop(market.id)
        # Free its tile
        self._empty_tiles.add(pos)
        # Delete the instance from the database
        market.delete()

    def _finish(self):
        """
        Reset the state of the players and record the players' score.
        This function is called at the end of each game in the main loop.
        :return: Nothing.
        """

        if self._game is not None:
            # Refresh the game from db
            self._game.refresh_from_db()

            # Update the game's state
            self._game.state = "F"

            # For each player
            for player in self._players:
                # Refresh the player from the database
                player.refresh_from_db()
                # Record the score
                score = Score(player=player, score=player.gold, game=self._game)
                score.save()
                commit()

                # Update the player's
                # Health
                player.health = DEFAULT_PLAYER_HEALTH
                # Strength
                player.strength = 1
                # State
                player.state = "I"
                # Gold
                player.gold = 0
                # Action
                player.action = ''
                # Update the database object
                player.save()
                commit()

            # Remove enemies, items, mines and markets from the board
            for m_id in dict(self._mines):
                try:
                    mine = Mine.objects.get(pk=m_id)
                    self._remove_mine(mine)
                except models.ObjectDoesNotExist as e:
                    self._logger.exception(e)
                    continue

            for e_id in dict(self._enemies):
                try:
                    enemy = Enemy.objects.get(pk=e_id)
                    self._remove_enemy(enemy)
                except models.ObjectDoesNotExist as e:
                    self._logger.exception(e)
                    continue

            for i_id in dict(self._items):
                try:
                    item = Item.objects.get(pk=i_id)
                    self._remove_item(item)
                except models.ObjectDoesNotExist as e:
                    self._logger.exception(e)
                    continue

            for m_id in dict(self._markets):
                try:
                    market = Market.objects.get(pk=m_id)
                    self._remove_market(market)
                except models.ObjectDoesNotExist as e:
                    self._logger.exception(e)
                    continue

            # Update the state of the game
            self._game.map.save()
            commit()
            self._game.save()
            commit()

        # Reset the content of the DungeonMaster's attributes
        self._game = None
        self._items = {}
        self._enemies = {}
        self._players = []
        self._walls = []
        self._mines = {}
        self._markets = {}
        self._empty_tiles = set([(x, y) for x in range(0, MAP_WIDTH) for y in range(0, MAP_HEIGHT)])
        self._trials = {}
        self._times = {}

    def main(self):
        """
        This is the main function of the Dungeon Master. It loops over the initialize, play and finish functions,
        consuming any game waiting in the database.
        If no game is waiting to be played, the main function will simply wait and check regularly for new games.
        :return: Nothing.
        """

        try:
            while True:
                # Initialize the game
                while not self._initialize():
                    # If no game is present just wait for a while
                    sleep(2)

                # Play the game
                self._play()

                # Sweep up after finishing the game
                self._finish()
        except KeyboardInterrupt:
            self._finish()
            self._logger.info("Closing the Dungeon Master as requested by the user.")
            exit(0)
        except BaseException as e:
            self._finish()
            self._logger.exception(e)
