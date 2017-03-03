#!/usr/bin/python
# -*- coding: utf-8 -*-
from string import ascii_uppercase, digits
from random import SystemRandom, choice


def format_msg(action, data=None, orig=None):
    """
    Given the parameters, generates a message to be sent to an Actor.
    :param action: The action the Actor should perform upon reception of the message.
    :param data: The information required for the completion of the action.
    :param orig: The original sender of the message if necessary (mainly used for ask requests).
    :return: dict. A formatted dictionary containing all the information.
    """

    return {'action': action, 'data': data, 'orig': orig}


def extract_msg(msg):
    """
    Extract that action, data and original sender from a correctly formatted message.
    :param msg: A dictionary formatted message.
    :return: Tuple. (action, data, orig)
    """

    return msg.get('action'), msg.get('data'), msg.get('orig')


def code_generator(size=15):
    """
    Generate a string of random uppercase and digits characters of a given length.
    :param size: The length of the string to generate.
    :return: String.
    """
    return ''.join([SystemRandom().choice(ascii_uppercase + digits) for _ in range(size)])

