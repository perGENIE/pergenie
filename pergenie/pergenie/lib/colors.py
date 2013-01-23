#!/usr/bin/env python

#
# colors.py
#

"""Print with colors.
    
    usage:
    print colors.red('aaa')

    black, red, green, yellow, blue, purple, cyan, white
"""

def getcolor(colorname):
    colors = {
        'clear': '\033[0m',
        'black': '\033[30m',
        'red': '\033[31m',
        'green': '\033[32m',
        'yellow': '\033[33m',
        'blue': '\033[34m',
        'purple': '\033[35m',
        'cyan': '\033[36m',
        'white': '\033[37m'
        }
    def func2(c):
        return colors[colorname] + str(c) + colors['clear']

    return func2

black  = getcolor('black')
red    = getcolor('red')
green  = getcolor('green')
yellow = getcolor('yellow')
blue   = getcolor('blue')
purple = getcolor('purple')
cyan   = getcolor('cyan')
white  = getcolor('white')

# a = "this is a test message"
# print red(a)
# print white(a)
# print cyan(a)
# print purple("test ") + yellow("message")
