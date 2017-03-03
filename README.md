# About Viking Doom

Viking Doom is an on-line rogue-like game centered around vikings (well, duh ...) that involves: gold, glory, a dragon (sorry, budget was low couldn't afford more than one) and lukewarm mead, but also a bit of Artificial Intelligence (AI). It is an epic quest designed to be played by your computer, which will have to take control of a hero and plow through hordes of skeletons and orcs in hopes of gold and glory. The goal? Gather as much gold as possible (at least more than your opponents). How to do that? As efficiently as possible. Armed with your best strategy, your axe and your shield, enter the competition and aim for the top (the top is where the mead is, or so I have heard).
Since Viking Doom is build around a client / server architecture and communication, with the game engine, relies on the HTTP protocol, it means that there are no restrictions regarding the programming language you should use to implement your bot. All you need to compete is a computer, good programming skills, an Internet connection and a brilliant strategy. Optionally, you can also ask your friends to help you in your quest for glory (but friends tend to be a rare supply these days).
The Viking Doom project has been made publicly available for two main reasons:
   1. So that participants can install a local version of the game and try their hand at the game in private, before entering the real competition.
   2. To provide a basis upon which other might improve and organize their own competitions. Yes, you heard (actually, read ... moving on) it correctly. You can use and/or modify Viking Doom to your heart content. Go nuts, make it your own and try to have fun in the process.

But Viking Doom is more than a simple game/website. It stems from an experiment (gone wrong ... horribly wrong) for a PhD project entitled: "The Role of Emotions in Autonomous Social Agents". The goal of this project is to understand what emotions are and how does the brain produce them? But far from being limited to only understanding, the project strives to build an artificial neuron based architecture that would allow agents (robots, virtual AIs and so on) to have and use emotions. The belief at the basis of this project is that emotions have evolved throughout history as a mean to improve an animal's (human included) survival and adaptive skills in dynamic environment. Artificial agents endowed with a similar mechanism would be able to generalize their knowledge over different tasks and reach higher levels of intelligence (yes like Skynet, but not necessarily evil). AI programs would no longer be specialized and Human-Robot Interaction (HRI) would be facilitated.

For more details about the whole project, how to write your bot and contact informations have a look around [Viking Doom](http://www.vikingdoom.com). Or download the project's official [Information Sheet](http://vikingdoom.com/static/game/viking_doom_information_sheet.pdf).

# Requirements

Viking Doom can more or less be split into three interdependent parts:
   1. A website: Where you can find all the content concerning the story, rules and technical documentation, as well as a form to register new users. The home page also has a live display of any game that is currently playing.
   2. The game engine: That is where the magic happens. Client computers communicate with the game engine to move heroes around. The game engine is also in charge of moving skeletons and upgrade caravans around, as well as, making sure that items and enemies are never in short supply.
   3. Finally, there is an example of a bot implemented in Python. The bot is very simple and only performs random movements, but still it keeps track of the game's state and make sure not to perform any forbidden action.

All three parts are implemented in python and make heavy use of [Django](https://www.djangoproject.com/), [Thespian](https://github.com/godaddy/Thespian), [Websockets](https://websockets.readthedocs.io/en/stable/) and [Requests](http://docs.python-requests.org/en/master/). Hence, the following required modules:
   1. Python version 3.4 or newer. It is really important, since the project relies on the Asyncio module, introduced in version 3.4, to display the currently playing game.
   2. Django: The project was developed with Django version 1.10, but newer version should also work.
   3. Django Rest Framework: Version 3.5.4 was used.
   4. Coreapi: Required by the Django Rest Framework.
   5. Thespian: A robust multi-process python implementation of the Actor pattern. Version 3.7.0 or newer is required, since features were introduced in the framework as a result of us building Viking Doom.
   6. Websockets: A simple library to manage real-time communication between the game engine and the client web browser. Version 3.2 or newer.

Since Viking Doom is based on Django, it is only natural that we need a database to store the users, games, scores and so much more. Django has many [backends](https://docs.djangoproject.com/en/1.10/ref/databases/) available when it comes to databases, so here you are free to choose your own, but be aware that the next section that guide you through the installation process will be using a MySQL database. For those interested by this configuration, you can add the two following modules to the list of requirements:
   1. MySQL / MariaDB
   2. Mysqlclient
For the others, you will be in charge of making sure that your database is correctly configured, accessible and that you have the right client library for Django to be able to read/write into it.

## Optional

Here are some modules that are not essential for the main Viking Doom application to run, but they might just make your life easier:
   1. Setproctitle: Used by thespian to set a nice looking title for its sub-processes. Makes results from `top` and `htop` commands more human-friendly.
   2. Requests (Only required if you intend to use the Random bot for testing): A neat little library providing all the functions you need to write a robust HTTP client in python.
   3. Ujson: An optimized library for encoding / decoding python objects into JSON strings. Python already has a built-in json module, but Ujson is simply faster.

# Installation

All great installation begin with a little bit of cloning. In this case you will have to clone the VikingDoom's project on your computer. Make sure that your user has read / write permissions to the directory in which VikingDoom will reside, then simply execute `$> git clone https://github.com/casparluc/VikingDoom.git`.

Installing all of the required and even the optional modules is quite easy, since they are all available through the python package manager. On Linux all you need to do is:
   1. Open a new terminal window.
   2. And type in the following commands (depending on your system, you might have to be root to execute those commands):
   ```
   $> pip3 install Django
   $> pip3 install coreapi
   $> pip3 install djangorestframework
   $> pip3 install thespian
   $> pip3 install websockets
   $> pip3 install requests
   $> pip3 install mysqlclient
   ```

Next, you will have to install and configure a database for use in Django. If you decided to go with MySQL, installing the basic database on Linux can be done through the distribution's package manager:

On Ubuntu:
   ```
   $> sudo apt-get install mariadb-common
   ```

On Arch Linux:
   ```
   $> sudo pacman -S mariadb
   ```

For other distributions and more on how to configure the database, you can find information on [MariaDB's website](https://mariadb.com/kb/en/mariadb/getting-installing-and-upgrading-mariadb/).
Once your database is configured and running, be sure to fill in your database's configuration details in Viking Doom's `VikingDoom/settings.py` file. There is a section dedicated to databases, where you will have to provide a name for you db, a user along with its password and the host and port of the machine running the database. Again, more information on how to set a database for a Django project can be found in [Django's documentation](https://docs.djangoproject.com/en/1.10/ref/settings/#databases).

While you are editing the `VikingDoom/settings.py` configuration file, there are three more settings that require your attention:
   1. `SECRET_KEY`: It is a string of 50 random characters used by Django to encrypt most of its communications. If you are unsure how to generate your own secret key, you can use a this dedicated [on-line tool](http://www.miniwebtool.com/django-secret-key-generator/).
   2. `STATIC_ROOT`: This should contain the absolute path to the folder `game/static/` that reside inside the VikingDoom directory you just cloned. On Linux systems this path might look something like: `/home/user/VikingDoom/game/static/`.
   3. `ADMINS`: Finally, almost done. This setting is optional if you only intend to use VikingDoom as a local server. But if you ever want to use it in production, `ADMINS` should be a list of the website's administrators along with their email addresses (e.g.: `[('John Smith', 'agent.smith@gmail.com'), ('Rial Tuto', 'tuto@vikingdoom.com')]`).

And for the last step, before using VikingDoom you will have to populate the database (for the moment it should be empty if you just did a fresh installation). In the root directory of the project you should see a file name `manage.py`. This script is a convenience offered by Django to literally manage many aspects of a project. In this instance all you need to do is to execute all the database migrations required by each applications. So, making sure your database is running and correctly configured, simply run: 
```
python3 manage.py migrate
```

And that is it. You are done for the installation process. Sorry it was quite long to get here, but from now on it will be fun all around.


# Testing

For testing purposes and to provide you with a basic example of what a bot might look like, a python implementation of a random strategy can be found in `bot/RandomBot.py`. But before you can have your fun there is a few things to launch.
Open a new terminal window and navigate into the root directory of the VikingDoom project. Once there, you can launch a HTTP server (only meant for testing, not production) by running the command:
```
python3 manage.py runserver
```
If you open a web-browser and go to the url `http://localhost:8000` you should land on the home page of the Viking Doom's website. Now go to the `Create Player` page and create at least four new users (each game has four players and a player can only subscribe to the same game once). Make sure to keep the user codes somewhere safe, since you will be using them for later testing.

In another terminal window and from the root directory of the VikingDoom project, run:
```
python3 game/actors/Init.py
```
To test your installation or your own strategy, the only thing left to do is launch four bots. If you are using the provided `RandomBot.py` script, all you need to do is:
```
python3 bot/RandomBot.py your_user_code_here
```
Were you might want to replace `your_user_code_here` with the codes you got when creating your players in the previous steps.

After the fourth player has joined the game, the game engine should launch a new match. If you go back to on the home page of the Viking Doom's website the game will be displayed in real-time.

# Issues

Any issue should be reported on the `issue` page. Please do try to give as much details, concerning your problem, as possible to speed up the debugging process.


Hope you will enjoy playing Viking Doom.
