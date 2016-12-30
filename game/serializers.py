#!/usr/bin/python
# -*- coding: utf-8 -*-

from rest_framework import serializers
from .models import *
from collections import OrderedDict


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email')


class EnemySerializer(serializers.ModelSerializer):
    class Meta:
        model = Enemy
        fields = ('id', 'health', 'pos_x', 'pos_y', 'dead', 'protected', 'type', 'strength', 'action')


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ('id', 'value', 'pos_x', 'pos_y', 'type', 'consumed')


class MarketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Market
        fields = ('id', 'pos_x', 'pos_y', 'type', 'price')


class PlayerSerializer(serializers.ModelSerializer):
    user = UserSerializer(required=True)

    class Meta:
        model = Player
        fields = ('id', 'user', 'pos_x', 'pos_y', 'spawn_x', 'spawn_y', 'health', 'gold', 'strength', 'state', 'code',
                  'action', 'last_action', 'last_answer_time', 'color')

    def create(self, validated_data):
        """
        Handle the creation of a new Player instance in the database.
        :param validated_data: The data sent by the client, after being validated by the framework.
        :return: Player. The newly created Player instance.
        """

        # Pop the information concerning the user
        user_data = validated_data.pop('user')
        # Create the user instance
        user = User.objects.create(**user_data)
        # Create the player instance
        player = Player.objects.create(user=user, **validated_data)
        # Return the newly created player instance
        return player

    def update(self, instance, validated_data):
        """
        Handle the update of a player instance in the database.
        :param instance: The old player instance.
        :param validated_data: The new values of the player attributes as sent by the client and validated.
        :return: Player. The updated Player instance.
        """

        # Pop the data concerning the user
        user_data = validated_data.pop('user')
        # Get the former instance user
        user = instance.user
        # Update the user
        user.username = user_data.get('username', user.username)
        user.email = user_data.get('email', user.email)
        user.firstname = user_data.get('firstname', user.firstname)
        user.lastname = user_data.get('lastname', user.lastname)
        user.save()

        # Update the player
        instance.pos_x = validated_data.get('pos_x', instance.pos_x)
        instance.pos_y = validated_data.get('pos_y', instance.pos_y)
        instance.spawn_x = validated_data.get('spawn_x', instance.spawn_x)
        instance.spawn_y = validated_data.get('spawn_y', instance.spawn_y)
        instance.health = validated_data.get('health', instance.health)
        instance.gold = validated_data.get('gold', instance.gold)
        instance.strength = validated_data.get('strength', instance.strength)
        instance.state = validated_data.get('state', instance.state)
        instance.code = validated_data.get('code', instance.code)
        instance.action = validated_data.get('action', instance.action)
        instance.last_action = validated_data.get('last_action', instance.last_action)
        instance.last_answer_time = validated_data.get('last_answer_time', instance.last_answer_time)
        instance.color = validated_data.get('color', instance.color)
        instance.save()

        # Return the updated instance
        return instance


class CustomPlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ('pos_x', 'pos_y', 'spawn_x', 'spawn_y', 'health', 'gold', 'strength', 'state', 'action',
                  'last_action')


class MineSerializer(serializers.ModelSerializer):
    owner = PlayerSerializer()
    guardian = EnemySerializer()

    class Meta:
        model = Mine
        fields = ('id', 'owner', 'pos_x', 'pos_y', 'gold_rate', 'guardian')


class BoardSerializer(serializers.ModelSerializer):
    enemy = EnemySerializer(many=True)
    item = ItemSerializer(many=True)
    mine = MineSerializer(many=True)
    market = MarketSerializer(many=True)

    class Meta:
        model = Board
        fields = ('id', 'str_map', 'img_path', 'width', 'height', 'enemy', 'item', 'mine', 'market')


class CustomBoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ('str_map', 'img_path', 'width', 'height')


class GameSerializer(serializers.ModelSerializer):
    map = BoardSerializer()
    player_1 = PlayerSerializer()
    player_2 = PlayerSerializer()
    player_3 = PlayerSerializer()
    player_4 = PlayerSerializer()

    class Meta:
        model = Game
        fields = ('id', 'map', 'player_1', 'player_2', 'player_3', 'player_4', 'turn', 'terminated', 'modified', 'url',
                  'code', 'state')


class CustomGameSerializer(serializers.ModelSerializer):
    map = CustomBoardSerializer()
    player_1 = CustomPlayerSerializer()
    player_2 = CustomPlayerSerializer()
    player_3 = CustomPlayerSerializer()
    player_4 = CustomPlayerSerializer()

    def to_representation(self, instance):
        # Serialize the Game as normal
        data = super(CustomGameSerializer, self).to_representation(instance)

        # Add an entry to the data for the current player
        your_hero = self.context['your_hero']
        serializer = CustomPlayerSerializer(your_hero)
        hero_data = OrderedDict(serializer.data)

        # Find out which player you are
        if instance.player_1 == your_hero:
            hero_data.update({'id': 1})
        elif instance.player_2 == your_hero:
            hero_data.update({'id': 2})
        elif instance.player_3 == your_hero:
            hero_data.update({'id': 3})
        elif instance.player_4 == your_hero:
            hero_data.update({'id': 4})

        # Insert the information about your hero to the data
        data.update({'your_hero': hero_data})

        # Return the serialized data
        return data

    class Meta:
        model = Game
        fields = ('map', 'player_1', 'player_2', 'player_3', 'player_4', 'turn', 'terminated', 'modified',
                  'url', 'code', 'state')


class ScoreSerializer(serializers.ModelSerializer):
    player = PlayerSerializer()
    game = GameSerializer()

    class Meta:
        model = Score
        fields = ('id', 'player', 'score', 'game')
