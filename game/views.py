from .serializers import *
from .models import *
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Sum
from string import ascii_uppercase, digits
from random import SystemRandom, choice
import json
import logging
from time import sleep
from math import floor

#################################################################################
########################## GLOBAL VARIABLES #####################################
#################################################################################

BASE_GAME_URL = "http://www.vikingdoom.com/game/play/"
BOARD_CONFIG_FILES = ['game/maps/json/0.json']  # Insert file names here for board config in json format

#################################################################################
########################## HELPER FUNCTIONS #####################################
#################################################################################


def code_generator(size=15):
    """
    Generate a string of random uppercase and digits characters of a given length.
    :param size: The length of the string to generate.
    :return: String.
    """
    return ''.join([SystemRandom().choice(ascii_uppercase + digits) for _ in range(size)])

#################################################################################
########################## CLASS BASED VIEWS ####################################
#################################################################################


class EnemyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Enemy.objects.all()
    serializer_class = EnemySerializer


class ItemViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class PlayerViewSet(viewsets.ModelViewSet):
    queryset = Player.objects.all()
    serializer_class = PlayerSerializer

    def perform_create(self, serializer):
        gen_code = code_generator(15)
        while len(Player.objects.filter(code__exact=gen_code)) > 0:
            gen_code = code_generator(15)
        serializer.save(code=gen_code)


class BoardViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer


class GameViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Game.objects.all()
    serializer_class = GameSerializer


class ScoreViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Score.objects.all()
    serializer_class = ScoreSerializer


class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class MineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Mine.objects.all()
    serializer_class = MineSerializer


class MarketViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Market.objects.all()
    serializer_class = MarketSerializer


class DungeonMasterView(APIView):
    """
    Define a single post method to manage the Game queue.
    """
    
    @transaction.atomic
    def put(self, request, player_code='', format=None):
        """
        Create a new game (without map) if necessary or simply add the player to an un-complete game.
        :param request: The request sent by the player containing its code.
        :param player_code: The code of the player associated with the current user.
        :param format: The format of the response (json, xml).
        :return: Json/Xml object containing the details of the Game the user was added to.
        """

        # Log the data received by the post method
        logger = logging.getLogger("Game.Views")
        logger.debug("A player (code: {}) asked for a new game.".format(player_code))

        # Query the player from the database
        player = get_object_or_404(Player, code=player_code)
        
        # Check that the player is not already playing another game
        if player.state != "P":
            # Retrieve the latest created game with a "Initializing" status
            games = Game.objects.filter(state__exact="I").order_by('id')
            if len(games) == 0:
                # Create a new game
                game = self._create_game(player)
            else:
                # Try adding the player to a game
                game = games.first()
                self._add_uniq_player(game, player)

            # Save the player
            player.save()
            # Save the game in the database
            game.save()

            # Initialize the serializer
            serializer = CustomGameSerializer(game, context={'your_hero': player})

            # Return the game data so far
            return Response(data=serializer.data, status=status.HTTP_201_CREATED)
        else:
            # Get the game the player is involved in
            game = Game.objects.filter(state__exact="P").first()
            # Serialize the game
            serializer = CustomGameSerializer(game, context={'your_hero': player})
            return Response(data=serializer.data, status=status.HTTP_200_OK)

    def post(self, request, game_code='', format=None):
        """
        Update the action field of the player.
        :param request: The request sent by the client browser.
        :param game_code: The code corresponding to the game instance.
        :param format: The format requested for the response (json/xml).
        :return: Json/xml object containing the details of the Game the user is playing.
        """

        # Log the data received by the post method
        logger = logging.getLogger("Game.Views")
        logger.debug("Received data for game {} from player: code = {}, action = {}".format(game_code,
                                                                                            request.data['code'],
                                                                                            request.data['action']))

        # Query the corresponding game from the database
        game = get_object_or_404(Game, code=game_code)
        # Record the modification time
        last_mod_time = game.modified

        # Check the game's status
        if game.state == "P":
            # Get all the data required for updating the player
            player_code = request.data['code']
            action = request.data['action']

            # Query the corresponding player object from the database
            player = get_object_or_404(Player, code=player_code)

            # Update the action field and save to the database
            player.action = action
            player.save()
            transaction.commit()

            # Wait until the game is updated to send information back
            cpt = 0
            while game.modified == last_mod_time and cpt < 100:
                del game.modified
                sleep(0.2)
                cpt += 1

            # Serialize the game
            serializer = CustomGameSerializer(game, context={'your_hero': player})

            # Return the game data so far
            return Response(data=serializer.data, status=status.HTTP_200_OK)
        elif game.state in ["W", "I"]:
            # If the game is in waiting state send back a 504
            return Response(status=status.HTTP_504_GATEWAY_TIMEOUT)
        else:
            # If the game is finished send back a 503 status
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def _create_game(self, player):
        """
        Create a new game instance in the database.
        :param player: An instance of the Player model.
        :return: Game. The new game instance.
        """

        # Generate a random code
        code = code_generator(15)
        # Build the url to access the game
        url = BASE_GAME_URL + code + "/"
        # Create a new map for the game
        try:
            board = self._get_board_from_conf_file()
        except ValueError:
            return Response(data="An error occurred while reading the configuration file for the map.",
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except FileNotFoundError:
            return Response(data="Could not find the configuration file.",
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except IOError:
            return Response(data="Could not read/access configuration file for the map.",
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        board.save()

        # Return the game object
        return Game(player_1=player, code=code, url=url, map=board)

    def _get_board_from_conf_file(self):
        """
        Read and initialize a new Board from random configuration file.
        :return: Board. The initialize board from the database.
        """
        # Get the configuration file to be used
        filename = choice(BOARD_CONFIG_FILES)

        # Read the configuration from the file
        with open(filename, "r") as conf_f:
            # Load the json data
            data = json.load(conf_f)
            # Query the string representation of the map and the path to the background image
            txt_file = data['str_map']
            img_path = data['img_path']

        # Get the string representation of the file
        with open(txt_file, "r") as txt_conf:
            str_map = txt_conf.readline()

        # Return the initialized board
        return Board(str_map=str_map, img_path=img_path)

    def _add_uniq_player(self, game, player):
        """
        Check if the player is not already in a given game before adding him.
        :param game: An instance of the Game model.
        :param player: An instance of the Player model.
        :return: Boolean. Return True if the player was added to the game, False otherwise.
        """

        # Check that the player is not already in the game
        if game.player_1 == player or game.player_2 == player or game.player_3 == player or game.player_4 == player:
            return False
        else:
            # Add the player in an empty spot
            if game.player_1 is None:
                game.player_1 = player
                return True
            if game.player_2 is None:
                game.player_2 = player
                return True
            if game.player_3 is None:
                game.player_3 = player
                return True
            if game.player_4 is None:
                game.player_4 = player
                game.state = "W"
                return True

#################################################################################
######################## FUNCTION BASED VIEWS ###################################
#################################################################################


@api_view(['GET'])
def now_playing(request):
    """ Get the latest created game. """

    try:
        now_playing = Game.objects.get(state__exact="P")
        serializer = GameSerializer(now_playing)
        return Response(serializer.data)
    except MultipleObjectsReturned:
        return Response(data="Too many objects retrieved from database. Only one game is expected to be running at"
                             " once.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    except ObjectDoesNotExist:
        return Response(data='There is no game playing at the moment.', status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Serves the home page with leaderboard and game display
def index_view(request):
    players = Player.objects.all()
    context = {'ranks': []}
    for player in players.iterator():
        # Get all the player's scores
        scores = Score.objects.filter(player__exact=player)
        if len(scores) != 0:
            tot_gold = float(scores.aggregate(Sum('score'))['score__sum'])
            # compute his rank
            rank = floor(tot_gold / len(scores))
            # Append the score to the list
            context['ranks'].append({'username': player.user.username, 'rank': rank})

    return render(request, 'game/index.html', context=context)


# Serves the rule page, which is static
def rules_view(request):
    return render(request, 'game/rules.html', {})


# Serves the doc and starter page, which is also static
def docs_view(request):
    return render(request, 'game/docs.html', {})

@transaction.atomic
# Serves a form for creating new a player
def new_player_view(request):
    try:
        username = request.POST['uname']
        first_name = request.POST['fname']
        last_name = request.POST['lname']
        email = request.POST['email']
        if User.objects.filter(username__exact=username).exists():
            context = {'error_message': "This username is not available anymore. Please choose another one."}
        elif User.objects.filter(first_name__exact=first_name).exists() and User.objects.filter(last_name__exact=last_name).exists():
            context = {'error_message': "You seem to already exist in our database.<br/> If this is an error, please"
                                        " contact the administrator."}
        else:
            user = User(username=username, first_name=first_name, last_name=last_name, email=email)
            user.save()
            code = code_generator(15)
            player = Player(user=user, code=code)
            player.save()
            context = {'message': code}
    except ValidationError:
        context = {'error_message': "An error occurred, while trying to create a new player for you."}
    except KeyError:
        context = {}
    return render(request, 'game/new_player.html', context=context)
