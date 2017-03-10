#!/usr/bin/python
# -*- coding: utf-8 -*-
from random import choice, randint
import requests
import logging
from time import sleep
from datetime import date
import ujson


class RandomBot:
    """
    This bot is a simple example of how to connect to and play VikingDoom.
    The for each turn, the bot will choose a random action from the list, without taking into account any wrong move.
    """

    def __init__(self, player_code=None):
        """
        Declare the player's code and its possible actions as the Bot's attributes.
        :param player_code: The code associated with the player you created.
        """
        if player_code is not None and isinstance(player_code, str):
            # Initialize the Bot's attributes
            self._player_code = player_code  # The code you get when subscribing on the VikingDoom website
            self._available_actions = ["N", "S", "E", "W", "I"]  # Possible actions for the player regardless of its surroundings

            # Configure a simple logger
            today = date.today()
            logging.basicConfig(level=logging.DEBUG, filename="logs/bot_{}_{}_{}_{}.log".format(today.day, today.month,
                                                                                                today.year, player_code))
            self._logger = logging.getLogger("RandomBot")

            # Initialize variables related to the hero and the game
            self._player_state = "I"
            self._game_state = "I"
            self._session = requests.Session()
        else:
            raise ValueError("Error: player_code cannot be empty.")

    def _request_game(self):
        """
        Request the server to include the player in the next game to be played.
        :return: String. The url to which the player's action will be sent when playing the game.
        """

        # Send a simple put request to the server and retrieve the result
        try:
            result = self._session.put("http://vikingdoom.com/game/new/{}/".format(self._player_code), timeout=30)
        except requests.ConnectTimeout as e:
            # Write an error message to the logs
            self._logger.exception("Connection timeout: {}".format(e))
            # And exit the bot
            exit(1)
        except requests.ConnectionError as e:
            # Write an error message to the logs
            self._logger.exception("An error occurred while connecting to the server: {}".format(e))
            # And exit the bot
            exit(2)

        # Check the response status.
        # If no exception occurred process the data sent back by the server
        json_data = ujson.loads(result.json())
        self._logger.debug("Game request successful: {}, {}".format(json_data, type(json_data)))
        self._game_state = json_data['state']
        self._player_state = json_data['your_hero']['state']

        # And return the url to play the game
        url = json_data['url']
        return url

    def _play(self, url):
        """
        In the case of the present bot, it will simply send random actions to the server until the end of the game. Or
        until the player is terminated.
        :return: Nothing.
        """

        # Loop until the game is Finished or the player is Terminated
        while self._game_state != "F":
            # Choose a random action
            action = choice(self._available_actions)

            # Format the payload required for the request
            payload = {'code': self._player_code, 'action': action}

            # Send the request
            try:
                r = self._session.post(url=url, data=payload, timeout=30)
            except requests.ConnectTimeout as e:
                # Write an error message to the logs
                self._logger.exception("Connection timeout: {}".format(e))
                # And exit the bot
                exit(1)
            except requests.ReadTimeout as e:
                # Write an error message to the logs
                self._logger.exception("The server took too long to answer our request: {}".format(e))
                # And exit the bot
                exit(2)
            except requests.ConnectionError as e:
                # Write an error message to the logs
                self._logger.exception("An error occurred while connecting to the server: {}".format(e))
                # And exit the bot
                exit(3)

            if r.status_code == 504:  # A status code of 504 indicate that the game has been put in the waiting queue
                sleep(0.8)
                continue
            elif r.status_code == 503 or r.status_code == 500:  # A status code of 503 indicate that the game is finished and you can no longer send actions
                self._game_state = "F"
                continue

            # Write the response in the logs
            self._logger.debug("Action successfully sent: {}".format(r.json()))
            # Check if the player has been terminated
            json_data = ujson.loads(r.json())
            self._game_state = json_data['state']
            hero = json_data['your_hero']
            self._player_state = hero['state']

            # Write the current score in the logs
            self._logger.debug("Current score: {}".format(hero['gold']))

        # Write the end of the game in the logs
        self._logger.debug("Game ended.")

    def main(self):
        """
        This is the main loop of the RandomBot. It will simply ask for a new game and play indefinitely.
        :return: Nothing
        """

        try:
            while True:
                # Ask for a new game
                url = self._request_game()

                # Play the game until completion
                self._play(url)

                # Sleep for a little while to make debugging easy
                sleep(randint(5, 15))
        except KeyboardInterrupt:
            exit(0)

if __name__ == "__main__":
    from sys import argv

    try:
        # Create an instance of the RandomBot class
        rnd_bot = RandomBot(argv[1])
    except ValueError as e:
        print(e)
        exit(1)

    # Let's play to infinity and beyond !!!
    rnd_bot.main()
