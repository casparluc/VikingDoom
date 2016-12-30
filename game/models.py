from django.db import models

# Define some global constants for ease of access
DEFAULT_ENEMY_HEALTH = 50
DEFAULT_PLAYER_HEALTH = 100
DEFAULT_ITEM_VALUE = 10
DEFAULT_MARKET_PRICE = 10
ENEMY_TYPE_CHOICES = [('skeleton', 'skeleton'), ('orc', 'orc'), ('dragon', 'dragon')]
ENEMY_ACTION_CHOICES = [('F', 'Fight'), ('I', 'Idle')]
ITEM_TYPE_CHOICES = [('potion', 'potion'), ('gold', 'purse'), ('big_gold', 'chest')]
MARKET_TYPE_CHOICES = [('potion_m', 'potion'), ('upgrade_m', 'upgrade')]
PLAYER_STATE_CHOICES = [('I', 'Initializing'), ('W', 'Waiting'), ('P', 'Playing'), ('D', 'Dead'), ('T', 'Terminated')]
PLAYER_ACTION_CHOICES = [('F', 'Fight'), ('I', 'Idle'), ('N', 'North'), ('S', 'South'), ('W', 'West'), ('E', 'East'),
                         ('B', 'Buy'), ('D', 'Drink')]
PLAYER_COLOR_CHOICES = [('blue', 'blue'), ('red', 'red'), ('green', 'green'), ('brown', 'brown')]
GAME_STATE_CHOICES = [('I', 'Initializing'), ('W', 'Waiting'), ('P', 'Playing'), ('F', 'Finished')]
MAP_WIDTH = 18  # In units of length (columns here)
MAP_HEIGHT = 18  # In units of length (rows here)


class User(models.Model):
    username = models.CharField(max_length=50)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField()


class Enemy(models.Model):
    health = models.IntegerField(default=DEFAULT_ENEMY_HEALTH)
    pos_x = models.IntegerField(default=0)
    pos_y = models.IntegerField(default=0)
    dead = models.BooleanField(default=False)
    protected = models.BooleanField(default=False)  # If the enemy protects a mine or not. Prevent deletion.
    type = models.CharField(choices=ENEMY_TYPE_CHOICES, max_length=50)
    strength = models.IntegerField(default=1)  # Multiplier for the damage dealt while in battle.
    action = models.CharField(choices=ENEMY_ACTION_CHOICES, max_length=2, default="I")


class Item(models.Model):
    value = models.IntegerField(default=DEFAULT_ITEM_VALUE)
    pos_x = models.IntegerField(default=0)
    pos_y = models.IntegerField(default=0)
    type = models.CharField(choices=ITEM_TYPE_CHOICES, max_length=15)
    consumed = models.BooleanField(default=False)


class Player(models.Model):
    user = models.OneToOneField('User', related_name='user', on_delete=models.CASCADE)
    pos_x = models.IntegerField(default=0)
    pos_y = models.IntegerField(default=0)
    spawn_x = models.IntegerField(default=0)
    spawn_y = models.IntegerField(default=0)
    health = models.IntegerField(default=DEFAULT_PLAYER_HEALTH)
    gold = models.IntegerField(default=0)
    strength = models.IntegerField(default=1)  # Multiplier for damage dealt while in battle.
    state = models.CharField(choices=PLAYER_STATE_CHOICES, max_length=1, default="I")
    code = models.CharField(max_length=15, blank=True)  # The pattern that will be used in any URL to identify the player (e.g. A2DFAS432DD).
    action = models.CharField(max_length=1, blank=True)
    last_action = models.CharField(max_length=1, blank=True)
    last_answer_time = models.TimeField(auto_now=True)
    color = models.CharField(choices=PLAYER_COLOR_CHOICES, max_length=6)

    def __str__(self):
        """
        Redefine the way in which the model will be printed.
        :return: String.
        """

        return "Player {}: P: ({}, {}), H: {}, G: {}, S: {}, A: {}".format(self.id,self.pos_x, self.pos_y, self.health,
                                                                           self.gold, self.state, self.action)


class Mine(models.Model):
    owner = models.ForeignKey(Player, related_name='player', on_delete=models.SET_NULL, null=True)
    pos_x = models.IntegerField(default=0)
    pos_y = models.IntegerField(default=0)
    gold_rate = models.IntegerField(default=5)
    guardian = models.ForeignKey(Enemy, related_name='guardian', on_delete=models.SET_NULL, null=True)


class Market(models.Model):
    pos_x = models.IntegerField(default=0)
    pos_y = models.IntegerField(default=0)
    type = models.CharField(choices=MARKET_TYPE_CHOICES, max_length=20)
    price = models.IntegerField(default=DEFAULT_MARKET_PRICE)


class Board(models.Model):
    str_map = models.CharField(max_length=1024, default='')
    img_path = models.CharField(max_length=1024, default='')
    width = models.IntegerField(default=MAP_WIDTH)
    height = models.IntegerField(default=MAP_HEIGHT)
    enemy = models.ManyToManyField(Enemy)
    item = models.ManyToManyField(Item)
    mine = models.ManyToManyField(Mine)
    market = models.ManyToManyField(Market)


class Game(models.Model):
    map = models.ForeignKey(Board, on_delete=models.SET_NULL, null=True)
    player_1 = models.ForeignKey(Player, related_name="player_1", on_delete=models.SET_NULL, null=True)
    player_2 = models.ForeignKey(Player, related_name="player_2", on_delete=models.SET_NULL, null=True)
    player_3 = models.ForeignKey(Player, related_name="player_3", on_delete=models.SET_NULL, null=True)
    player_4 = models.ForeignKey(Player, related_name="player_4", on_delete=models.SET_NULL, null=True)
    turn = models.IntegerField(default=0)
    terminated = models.BooleanField(default=False)
    modified = models.DateTimeField(auto_now=True)
    url = models.CharField(max_length=256, default='http://127.0.0.1/vikingdoom/')
    code = models.CharField(max_length=15, blank=True)
    state = models.CharField(max_length=1, default='I', choices=GAME_STATE_CHOICES)


class Score(models.Model):
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    score = models.IntegerField(default=0)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
