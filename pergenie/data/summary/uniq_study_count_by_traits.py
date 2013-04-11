#!/usr/bin/env python
# -*- coding: utf-8 -*-

# from pprint import pprint
# from operator import itemgetter

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
    meta_analysis_count = {}

    for trait in traits_list:
        records = catalog.find({'trait': trait})

        uniq_studies = set()
        for record in records:
            uniq_studies.update([record['study']])

        # count `meta-analysis`
        tmp_count = 0
        for study in uniq_studies:
            if 'meta-analysis' in study:
                tmp_count += 1

        uniq_count[trait] = len(uniq_studies)
        meta_analysis_count[trait] = tmp_count

    # sort by counts of uniq studies
    print 'uniq_count', 'meta_analysis_count', 'study'
    for result in sorted(uniq_count.items(), key=lambda x: x[1]):
        print _color(result[1]), _color(meta_analysis_count[result[0]]), result[0]


if __name__ == '__main__':
    _main()
