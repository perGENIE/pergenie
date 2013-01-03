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
    color_map = {debug : {color: 'grey', attrs: ['bold'])},
                 info : {color: 'white'},
                 warn: {color: 'yellow', attrs: ['bold']},
                 error: {color: 'red'},
                 fatal: {color: 'red', attrs: ['bold']},
                 }
    
    def __init__(self, logger):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG) ###
        self.stdout = logging.StreamHandler()
        self.stdout.setLevel(logging.DEBUG) ###
        self.stdout.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
        self.logger.addHandler(self.stdout)

    def __getattr__(self, status):
        if status in ('debug', 'info', 'warn', 'error', 'fatal'):
            return lambda s, *args: getattr(self.logger, status)(
                colored(s, **self.colormap[status]), *args)

        return getattr(self.logger, status)

if __name__ == '__main__':
    log = getColorLogger()

    log.debug("booooring . . .")
    log.info("pleasing anecdote")
    log.warn("awkward utterance")
    log.error("drunken rudeness")

