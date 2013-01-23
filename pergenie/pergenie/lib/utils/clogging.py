#!/usr/bin/env python2.7
# -*- coding:utf-8 -*-

""""
ANSI colored Python logging.(color_log.py)

  * Original Public Clone URL: git://gist.github.com/1238935.git
  * Original Author: brainsik
"""

import logging
from termcolor import colored

class getColorLogger(object):
    def __init__(self, name):
        self.color_map = {'debug' : {'color': 'grey', 'attrs': ['bold']},
                 'info' : {'color': 'white'},
                 'warn': {'color': 'yellow', 'attrs': ['bold']},
                 'error': {'color': 'red'},
                 'critical': {'color': 'red', 'attrs': ['bold']}
                 }
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG) ###
        self.stdout = logging.StreamHandler()
        self.stdout.setLevel(logging.DEBUG) ###
        self.stdout.setFormatter(logging.Formatter('%(asctime)s %(name)s [%(levelname)s] %(message)s'))
        self.logger.addHandler(self.stdout)

    def __getattr__(self, status):
        if status in ('debug', 'info', 'warn', 'error', 'critical'):
            return lambda msg, *args: getattr(self.logger, status)(
                colored(msg, **self.color_map[status]), *args)


if __name__ == '__main__':
    log = getColorLogger(__name__)

    log.debug("booooring . . .")
    log.info("pleasing anecdote")
    log.warn("awkward utterance")
    log.error("drunken rudeness")
