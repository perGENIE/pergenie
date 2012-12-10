import os

def touch(filename, times=None):
    with file(filename, 'a'):
        os.utime(filename, times)
