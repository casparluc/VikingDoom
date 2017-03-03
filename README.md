# Introduction/About/Viking Doom

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

