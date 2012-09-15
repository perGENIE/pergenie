#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import argparse
import time
import csv
import re
import readline        

class WeblioEng2Ja(object):
    def __init__(self, path_to_eng2ja, path_to_eng2ja_plus):
        self.eng2ja = {}

        print 'Loading eng2ja.txt...'
        start = time.time()

        with open(path_to_eng2ja, 'rb') as fin:
            for record in csv.DictReader(fin, delimiter='/'):
                self.eng2ja[record['eng']] = record['ja']
        with open(path_to_eng2ja_plus, 'rb') as fin:
            for record in csv.DictReader(fin, delimiter='/'):
                self.eng2ja[record['eng']] = record['ja']

        end = time.time()
        print '... done ({} secs)'.format(end - start)

    def test(self):
        print '{0}: {1}'.format("Alzheimer's desease", self.eng2ja.get("Alzheimer's desease"))
        print '{0}: {1}'.format('アルツハイマー病', self.eng2ja.get('アルツハイマー病'))

    def get(self, raw_query):
        raw_result = self.eng2ja.get(raw_query)
        if raw_result:
            return raw_result
        else:
            return self.eng2ja.get(raw_query.lower())

    def split_get(self, raw_query):
        result = ""
        split_query = raw_query.split()
        for query in split_query:
            if self.get(query):
                result += self.get(query)
        return result

    def try_get(self, raw_query):
        if self.get(raw_query):
            return self.get(raw_query)
        else:
            return self.split_get(raw_query)

def main():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('path_to_eng2ja')
    parser.add_argument('path_to_eng2ja_plus')
    args = parser.parse_args()

    eng2ja = WeblioEng2Ja(args.path_to_eng2ja, args.path_to_eng2ja_plus)
    eng2ja.test()

    # ---------
    # InterFace
    while True:
        try:
            raw_query = raw_input('Query> ')
        except EOFError:
            break
        
        print '.get()', eng2ja.get(raw_query)
        print '.split_get()', eng2ja.split_get(raw_query)
        print '.try_get()', eng2ja.try_get(raw_query)


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    main()
