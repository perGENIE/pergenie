# -*- coding: utf-8 -*-

import os

try:
   import cPickle as pickle
except ImportError:
   import pickle

def pickle_dump_obj(obj, fout_name):
    with open(fout_name, 'wb') as fout:
        pickle.dump(obj, fout, protocol=2)

def pickle_load_obj(fin_name):
    with open(fin_name, 'rb') as fin:
        obj = pickle.load(fin)
    return obj


def touch(filename, times=None):
    """Touch <filename>
    """

    with file(filename, 'a'):
        os.utime(filename, times)
