#!/usr/bin/python
# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from game.DungeonMaster import DungeonMaster


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        Simply create an instance of the DungeonMaster and run it ad vitam eternam.
        :param args: Any passed argument will be ignored.
        :param options: Any passed option will be ignored.
        :return: Nothing.
        """

        # Create an instance of the dungeonMaster
        dg = DungeonMaster()
        # Inform the user about the method for closing the command
        self.stdout.write("Press CTRL-C to stop the Dungeon Master from playing more game.\n")
        # Run, baby! Run!
        dg.main()
