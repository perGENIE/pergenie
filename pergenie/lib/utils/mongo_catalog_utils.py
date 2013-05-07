#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import datetime
from pprint import pprint
import shutil
import glob

import pymongo


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--drop')
    parser.add_argument('--show', action='store_true')
    args = parser.parse_args()

    with pymongo.Connection() as connection:
        db = connection['pergenie']

        if args.show:
            pprint([collection_name for collection_name in db.collection_names() if collection_name.startswith('catalog.')])
            pprint(list(db['catalog_info'].find()))
            print '#latest catalog records:', db['catalog'][str(db['catalog_info'].find_one({'status': 'latest'})['date'].date()).replace('-', '_')].count()

        if args.drop:
            target = args.drop
            print '{} ...will be deleted'.format(target)

            wait = raw_input('y/n > ')

            if wait == 'y':
                db.drop_collection(target)
                pprint([collection_name for collection_name in db.collection_names() if collection_name.startswith('catalog.')])
                pprint(list(db['catalog_info'].find()))
                print '#latest catalog records:', db['catalog'][str(db['catalog_info'].find_one({'status': 'latest'})['date'].date()).replace('-', '_')].count()

            latest = db['catalog_info'].find_one({'status': 'latest'})
            prev = db['catalog_info'].find_one({'status': 'prev'})

            y, m, d = target.split('.')[1].split('_')
            tmp_datetime = datetime.datetime(int(y), int(m), int(d))
            print tmp_datetime
            if tmp_datetime == latest['date']:
                db['catalog_info'].update({'status': 'latest'}, {"$set": {'date': prev['date']}})
                db['catalog_info'].remove({'status': 'prev'})
            elif tmp_datetime == prev['date']:
                db['catalog_info'].remove({'status': 'prev'})


if __name__ == '__main__':
    _main()
