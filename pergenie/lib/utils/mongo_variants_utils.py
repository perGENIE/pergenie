#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import os
import pymongo
from pprint import pprint
import shutil
import glob

UPLOAD_DIR = '/tmp/pergenie/upload'


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--drop', help='drop variants of [user_id]')
    parser.add_argument('--dry', action='store_true')
    parser.add_argument('--show', action='store_true', help='show variants')
    args = parser.parse_args()

    with pymongo.Connection() as connection:  # port=settings.MONGO_PORT
        db = connection['pergenie']

        if args.drop:
            # `collection` of variant
            targets = []
            for collection_name in db.collection_names():
                if collection_name.startswith('variants.{0}.'.format(args.drop)):
                    targets.append(collection_name)

            pprint(targets)
            print '...will be deleted'

            wait = raw_input('y/n > ')

            if not args.dry and wait == 'y':
                for target in targets:
                    db.drop_collection(target)
                after = [collection_name for collection_name in db.collection_names() if collection_name.startswith('variants.{0}.'.format(args.drop))]
                pprint(after)

            # `document` in data_info
            targets_in_data_info = list(db['data_info'].find({'user_id': args.drop}))
            pprint(targets_in_data_info)
            print '...will be deleted'

            wait = raw_input('y/n > ')

            if not args.dry and wait == 'y':
                targets_in_data_info = db['data_info'].remove({'user_id': args.drop})

                after = list(db['data_info'].find({'user_id': args.drop}))
                pprint(after)

            # rm `dir`
            target_dir = glob.glob(os.path.join(UPLOAD_DIR, args.drop))
            pprint(target_dir)
            print '...will be deleted'

            wait = raw_input('y/n > ')

            if not args.dry and wait == 'y':
                if len(target_dir) == 1:
                    shutil.rmtree(target_dir[0]) # rm -r <dir>
            target_dir = glob.glob(os.path.join(UPLOAD_DIR, args.drop))
            pprint(target_dir)

        elif args.show:
            variants = [collection_name for collection_name in db.collection_names() if collection_name.startswith('variants.')]
            print 'variants:'
#             pprint(variants)

            pprint([(collection_name, db[collection_name].count()) for collection_name in variants])

            data_info_found = list(db['data_info'].find())
            print 'data_info_found:'
            pprint(data_info_found)

            target_dir = glob.glob(os.path.join(UPLOAD_DIR, '*', '*'))
            print 'target_dir:'
            pprint(target_dir)

if __name__ == '__main__':
    _main()
