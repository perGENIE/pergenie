#!/usr/bin/env python
# -*- coding: utf-8 -*-

# from pprint import pprint
# from operator import itemgetter
from collections import defaultdict

import cPickle as pickle
import pymongo

from termcolor import colored

def _color(number):
    if number == 0:
        return colored(str(number), 'grey')
    elif 2 > number >= 1:
        return colored(str(number))
    elif 3 > number >= 2:
        return colored(str(number), 'blue')
    elif number >= 3:
        return colored(str(number), 'red')


def _main():
    con = pymongo.Connection()
    db = con['pergenie']

    # TODO: get latest automatically
    #     latest =  db['catalog_info'].find_one({'status': 'latest'})['date']
    catalog = db['catalog.2013_04_10']
    print catalog.count()

    #
    traits_list = pickle.load(open('trait_list.p'))

    # count uniq studies for each traits
    uniq_count = {}

    for trait in traits_list:
        records = catalog.find({'trait': trait})

        uniq_studies = set()
        for record in records:
            uniq_studies.update([record['study']])

        uniq_count[trait] = len(uniq_studies)

    # histo-gram
    uniq_count_count = defaultdict(int)
    for result in sorted(uniq_count.items(), key=lambda x: x[1]):
        uniq_count_count[result[1]] += 1

    print 'traits_count', 'study_count'
    for k,v in uniq_count_count.items():
        print _color(k), v


if __name__ == '__main__':
    _main()
