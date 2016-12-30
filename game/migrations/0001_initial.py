# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2016-12-28 22:55
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Board',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('str_map', models.CharField(default='', max_length=1024)),
                ('img_path', models.CharField(default='', max_length=1024)),
                ('width', models.IntegerField(default=18)),
                ('height', models.IntegerField(default=18)),
            ],
        ),
        migrations.CreateModel(
            name='Enemy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('health', models.IntegerField(default=50)),
                ('pos_x', models.IntegerField(default=0)),
                ('pos_y', models.IntegerField(default=0)),
                ('dead', models.BooleanField(default=False)),
                ('protected', models.BooleanField(default=False)),
                ('type', models.CharField(choices=[('skeleton', 'skeleton'), ('orc', 'orc'), ('dragon', 'dragon')], max_length=50)),
                ('strength', models.IntegerField(default=1)),
                ('action', models.CharField(choices=[('F', 'Fight'), ('I', 'Idle')], default='I', max_length=2)),
            ],
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('turn', models.IntegerField(default=0)),
                ('terminated', models.BooleanField(default=False)),
                ('modified', models.DateTimeField(auto_now=True)),
                ('url', models.CharField(default='http://127.0.0.1/vikingdoom/', max_length=256)),
                ('code', models.CharField(blank=True, max_length=15)),
                ('state', models.CharField(choices=[('I', 'Initializing'), ('W', 'Waiting'), ('P', 'Playing'), ('F', 'Finished')], default='I', max_length=1)),
                ('map', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='game.Board')),
            ],
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.IntegerField(default=10)),
                ('pos_x', models.IntegerField(default=0)),
                ('pos_y', models.IntegerField(default=0)),
                ('type', models.CharField(choices=[('potion', 'potion'), ('gold', 'purse'), ('big_gold', 'chest')], max_length=15)),
                ('consumed', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Market',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pos_x', models.IntegerField(default=0)),
                ('pos_y', models.IntegerField(default=0)),
                ('type', models.CharField(choices=[('potion_m', 'potion'), ('upgrade_m', 'upgrade')], max_length=20)),
                ('price', models.IntegerField(default=10)),
            ],
        ),
        migrations.CreateModel(
            name='Mine',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pos_x', models.IntegerField(default=0)),
                ('pos_y', models.IntegerField(default=0)),
                ('gold_rate', models.IntegerField(default=5)),
                ('guardian', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='guardian', to='game.Enemy')),
            ],
        ),
        migrations.CreateModel(
            name='Player',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pos_x', models.IntegerField(default=0)),
                ('pos_y', models.IntegerField(default=0)),
                ('spawn_x', models.IntegerField(default=0)),
                ('spawn_y', models.IntegerField(default=0)),
                ('health', models.IntegerField(default=100)),
                ('gold', models.IntegerField(default=0)),
                ('strength', models.IntegerField(default=1)),
                ('state', models.CharField(choices=[('I', 'Initializing'), ('W', 'Waiting'), ('P', 'Playing'), ('D', 'Dead'), ('T', 'Terminated')], default='I', max_length=1)),
                ('code', models.CharField(blank=True, max_length=15)),
                ('action', models.CharField(blank=True, max_length=1)),
                ('last_action', models.CharField(blank=True, max_length=1)),
                ('last_answer_time', models.TimeField(auto_now=True)),
                ('color', models.CharField(choices=[('blue', 'blue'), ('red', 'red'), ('green', 'green'), ('brown', 'brown')], max_length=6)),
            ],
        ),
        migrations.CreateModel(
            name='Score',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('score', models.IntegerField(default=0)),
                ('game', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.Game')),
                ('player', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='game.Player')),
            ],
        ),
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=50)),
                ('first_name', models.CharField(max_length=50)),
                ('last_name', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=254)),
            ],
        ),
        migrations.AddField(
            model_name='player',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='user', to='game.User'),
        ),
        migrations.AddField(
            model_name='mine',
            name='owner',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='player', to='game.Player'),
        ),
        migrations.AddField(
            model_name='game',
            name='player_1',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='player_1', to='game.Player'),
        ),
        migrations.AddField(
            model_name='game',
            name='player_2',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='player_2', to='game.Player'),
        ),
        migrations.AddField(
            model_name='game',
            name='player_3',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='player_3', to='game.Player'),
        ),
        migrations.AddField(
            model_name='game',
            name='player_4',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='player_4', to='game.Player'),
        ),
        migrations.AddField(
            model_name='board',
            name='enemy',
            field=models.ManyToManyField(to='game.Enemy'),
        ),
        migrations.AddField(
            model_name='board',
            name='item',
            field=models.ManyToManyField(to='game.Item'),
        ),
        migrations.AddField(
            model_name='board',
            name='market',
            field=models.ManyToManyField(to='game.Market'),
        ),
        migrations.AddField(
            model_name='board',
            name='mine',
            field=models.ManyToManyField(to='game.Mine'),
        ),
    ]
