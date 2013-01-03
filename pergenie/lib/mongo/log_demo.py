#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import sys
import os
dirname = os.path.dirname
BASE_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, 'lib'))

from utils import clogging

def _main():
    log = clogging.getColorLogger()
    
    log.info('path_to_LD_data_dir {}'.format(1))
    log.warn('kill')

if __name__ == '__main__':
    _main()
