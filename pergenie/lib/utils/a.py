t#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse








def _main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('infile', help='')
    args = parser.parse_args()

    with open(args.infile) as fin:
        for line in fin:
            pass




if __name__ == '__main__':
    _main()
