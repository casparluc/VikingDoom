from game.serializers import *
from game.models import *
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.shortcuts import render
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist, ValidationError
from django.db import transaction
from django.db.models import Sum
from string import ascii_uppercase, digits
from random import SystemRandom
from math import floor
from thespian.actors import *
from game.actors.LookupActor import LookupActor
from game.actors.PlayerLookupActor import PlayerLookupActor
from game.actors.Settings import LOOKUP_NAME, PLAYER_LOOKUP_NAME
from game.actors.utils import format_msg, extract_msg
import logging
from time import sleep

#################################################################################
########################## HELPER FUNCTIONS #####################################
#################################################################################


def code_generator(size=15):
    """
    Generate a string of random uppercase and digits characters of a given length.
    :param size: The length of the string to generate.
    :return: String.
    """
    code = ''.join([SystemRandom().choice(ascii_uppercase + digits) for _ in range(size)])
    while User.objects.filter(code__exact=code).count() > 0:
        code = ''.join([SystemRandom().choice(ascii_uppercase + digits) for _ in range(size)])
    return code

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

    def perform_create(self, serializer):
        gen_code = code_generator()
        serializer.save(code=gen_code)


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

    def __init__(self):
        """
        Declare an ActorSystem and LookupActor for later use.
        """

        # Initialize the parent class
        super(DungeonMasterView, self).__init__()

        # Declare the ActorSystem and LookupActor
        self._asys = ActorSystem("multiprocTCPBase")

    def put(self, request, player_code='', format=None):
        """
        Create a new game (without map) if necessary or simply add the player to an un-complete game.
        :param request: The request sent by the player containing its code.
        :param player_code: The code of the player associated with the current user.
        :param format: The format of the response (json, xml).
        :return: Json/Xml object containing the details of the Game the user was added to.
        """

        # Check that the user exist in the database
        if not User.objects.filter(code__exact=player_code).exists():
            return Response(data="User does not exist in the database.", status=status.HTTP_404_NOT_FOUND)

        # Ask for the ActorAddress of a game the user is not subscribed to
        data = None
        subscribed = []
        lookup = self._asys.createActor(LookupActor, globalName=LOOKUP_NAME)

        while data is None:
            # Initialize both game_addr and data
            game_addr = None
            while game_addr is None or not isinstance(game_addr, ActorAddress):
                with self._asys.private() as thrd_asys:
                    game_addr = thrd_asys.ask(lookup, format_msg('addr', data={'subscribed': subscribed}), 5)

                # Let the server breath a little bit
                if game_addr is None:
                    sleep(2)

            # Save the game address in case the code loops
            subscribed.append(game_addr)

            # Ask the game to create a new player for us
            with self._asys.private() as thrd_asys:
                data = thrd_asys.ask(game_addr, format_msg('add_player', data={'code': player_code}), 5)

            # Let the server breath a little
            if data is None:
                sleep(2)

        # Extract all information from the response
        game_state = data.get('game_state')

        # Return the game data so far
        return Response(data=game_state, status=status.HTTP_201_CREATED)

    def post(self, request, game_code='', format=None):
        """
        Update the action field of the player.
        :param request: The request sent by the client browser.
        :param game_code: The code corresponding to the game instance.
        :param format: The format requested for the response (json/xml).
        :return: Json/xml object containing the details of the Game the user is playing.
        """

        # Extract all required information
        player_action = request.data['action']
        player_code = request.data['code']

        # Make sure the user exist in database
        if not User.objects.filter(code__exact=player_code).exists():
            return Response(data="User does not exist in the database.", status=status.HTTP_404_NOT_FOUND)

        # Ask for the address of the player actor
        lookup = self._asys.createActor(PlayerLookupActor, globalName=PLAYER_LOOKUP_NAME)

        # Get the player's address
        cpt = 0
        player_addr = None
        while cpt < 3 and player_addr is None and not isinstance(player_addr, ActorAddress):
            with self._asys.private() as thrd_asys:
                player_addr = thrd_asys.ask(lookup, format_msg('look', data={'game_code': game_code, 'user_code': player_code}), 3)  # Timeout of 3 seconds
            # Only sleep if we did not get the address
            if player_addr is None:
                sleep(2)

        # If we still could not find the player's address
        if player_addr is None or not isinstance(player_addr, ActorAddress):
            # An error occurred send back a 404
            return Response(data="An error occurred while looking for your player.", status=status.HTTP_404_NOT_FOUND)

        # Ask the PlayerActor for the next action
        with self._asys.private() as thrd_asys:
            res = thrd_asys.ask(player_addr, format_msg('next_action', data={'action': player_action, 'code': player_code}), 3)  # Timeout of 3 seconds

        if res is None:  # The player was terminated or the game is finished
            # If the game is finished send back a 503 status
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # Extract information from the result
        action, data, orig = extract_msg(res)
        if action == 'error':
            # If the game is in waiting state send back a 504
            return Response(data=data, status=status.HTTP_504_GATEWAY_TIMEOUT)

        if action == 'ok':
            # All went well
            return Response(data=data, status=status.HTTP_200_OK)

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
    context = {'ranks': []}
    for user in User.objects.all().iterator():
        # Get all the player's scores
        scores = Score.objects.filter(user__exact=user)
        if len(scores) != 0:
            tot_gold = float(scores.aggregate(Sum('score'))['score__sum'])
            # compute his rank
            rank = floor(tot_gold / len(scores))
            # Append the score to the list
            context['ranks'].append({'username': user.username, 'rank': rank})

    return render(request, 'game/index.html', context=context)


# Serves the rule page, which is static
def rules_view(request):
    return render(request, 'game/rules.html', {})


# Serves the doc and starter page, which is also static
def docs_view(request):
    return render(request, 'game/docs.html', {})


# Serves the about page, which is static
def about(request):
    return render(request, 'game/about.html', {})


@transaction.atomic
# Serves a form for creating new a player
def new_player_view(request):
    try:
        username = request.POST['uname']
        first_name = request.POST['fname']
        last_name = request.POST['lname']
        email = request.POST['email']

        # Remove any whitespace from the information to check if someone has been naughty
        c_username = username.replace(' ', '')
        c_f_name = first_name.replace(' ', '')
        c_l_name = last_name.replace(' ', '')
        c_email = email.replace(' ', '')

        # Send back some not too pleasing comment
        if not c_username or not c_f_name or not c_l_name or not c_email:
            context = {'error_message': "Please do try to enter valid information when registering."}
        elif User.objects.filter(username__exact=username).exists():
            context = {'error_message': "This username is not available anymore. Please choose another one."}
        elif User.objects.filter(first_name__exact=first_name).exists() and User.objects.filter(last_name__exact=last_name).exists():
            context = {'error_message': "You seem to already exist in our database. If this is an error, please"
                                        " contact the administrator."}
        else:
            code = code_generator()
            user = User(username=username, first_name=first_name, last_name=last_name, email=email, code=code)
            user.save()
            context = {'message': code}
    except ValidationError:
        context = {'error_message': "An error occurred, while trying to create a new player for you."}
    except KeyError:
        context = {}
    return render(request, 'game/new_player.html', context=context)
