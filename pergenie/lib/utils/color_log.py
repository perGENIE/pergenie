#!/usr/bin/env python2.7
# -*- coding:utf-8 -*-

"""
color_log.py

* Description: ANSI colored Python logging
* Public Clone URL: git://gist.github.com/1238935.git
* Author: brainsik

* Require: termcolor
"""

import logging
from termcolor import colored

class ColorLogging(object):
    colormap = dict(
        debug=dict(color='grey', attrs=['bold']),
        info=dict(color='white'),
        warn=dict(color='yellow', attrs=['bold']),
        warning=dict(color='yellow', attrs=['bold']),
        error=dict(color='red'),
        critical=dict(color='red', attrs=['bold']),
        )

    def __init__(self, logger):
        self._log = logger

    def __getattr__(self, name):
        if name in ['debug', 'info', 'warn', 'warning', 'error', 'critical']:
            return lambda s, *args: getattr(self._log, name)(
                colored(s, **self.colormap[name]), *args)

        return getattr(self._log, name)

if __name__ == '__main__':
    log = ColorLogging(logging.getLogger(__name__))

    log.setLevel(logging.DEBUG)
    stdout = logging.StreamHandler()
    stdout.setLevel(logging.DEBUG)
    stdout.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
    log.addHandler(stdout)

    log.debug("booooring . . .")
    log.info("pleasing anecdote")
    log.warn("awkward utterance")
    log.error("drunken rudeness")

