#!/usr/bin/python
# -*- coding: utf-8 -*-

from rest_framework import serializers
from game.models import *
from collections import OrderedDict


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'email', 'code')

    def create(self, validated_data):
        """
        Handle the creation of a new User instance in the database.
        :param validated_data: The data sent by the client and validated by the framework.
        :return: User. The new user instance.
        """

        return User.objects.create(**validated_data)

    def update(self, instance, validated_data):
        """
        Handle the update of a User instance in database.
        :param instance: The existing instance to update.
        :param validated_data: The data sent by the client and validated by the framework.
        :return: User. The updated instance.
        """

        # Update the instance's fields
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        # Save the instance in database
        instance.save()
        # Return the instance
        return instance


class EnemySerializer(serializers.ModelSerializer):
    class Meta:
        model = Enemy
        fields = ('id', 'health', 'pos_x', 'pos_y', 'protected', 'type', 'strength', 'action')


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ('id', 'value', 'pos_x', 'pos_y', 'type', 'consumed')


class MarketSerializer(serializers.ModelSerializer):
    class Meta:
        model = Market
        fields = ('id', 'pos_x', 'pos_y', 'type', 'price')


class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ('id', 'pos_x', 'pos_y', 'spawn_x', 'spawn_y', 'health', 'gold', 'strength', 'state', 'action',
                  'last_action', 'color', 'hero_id')


class CustomPlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = ('hero_id', 'pos_x', 'pos_y', 'spawn_x', 'spawn_y', 'health', 'gold', 'strength', 'state', 'action')


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
        fields = ('str_map', 'width', 'height')


class GameSerializer(serializers.ModelSerializer):
    map = BoardSerializer()
    players = PlayerSerializer(many=True)

    class Meta:
        model = Game
        fields = ('id', 'map', 'players', 'turn', 'url', 'code', 'state')


class CustomGameSerializer(serializers.ModelSerializer):
    map = CustomBoardSerializer()
    players = CustomPlayerSerializer(many=True)

    def to_representation(self, instance):
        # Serialize the Game as normal
        data = super(CustomGameSerializer, self).to_representation(instance)

        # Add an entry to the data for the current player
        your_hero = self.context.get('your_hero')
        if your_hero is not None:
            serializer = CustomPlayerSerializer(your_hero)
            hero_data = OrderedDict(serializer.data)

            # Insert the information about your hero to the data
            data.update({'your_hero': hero_data})

        # Return the serialized data
        return data

    class Meta:
        model = Game
        fields = ('map', 'players', 'turn', 'url', 'code', 'state')


class ScoreSerializer(serializers.ModelSerializer):
    player = PlayerSerializer()
    game = GameSerializer()

    class Meta:
        model = Score
        fields = ('id', 'player', 'score', 'game')
