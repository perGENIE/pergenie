#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

#
import sys
import os
dirname = os.path.dirname
BASE_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, 'lib'))

# logging with colors
import logging
from utils import color_log


# log.setLevel(logging.DEBUG)
# stdout = logging.StreamHandler()
# stdout.setLevel(logging.DEBUG)
# stdout.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
# log.addHandler(stdout)

def _main():
    log = color_log.ColorLogging(logging.getLogger(__name__))
    
    log.info('path_to_LD_data_dir {}'.format(1))
    log.warn('kill')

if __name__ == '__main__':
    _main()
