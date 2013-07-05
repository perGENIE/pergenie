#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This script will be used as cron job:

$ python cron.py /path/to/datadir

1.
Suppose users put genome data on:
/somewhere/pergenie/uploaded/username/fileformat/*.ext

2.
Cron to import/update/delete each file into DB.
"""

import sys, os
import argparse
import glob
import datetime
import pymongo
from common import clean_file_name
from mongo.import_variants import import_variants

# FIXME:
sys.path.insert(0, '../pergenie/')
import socket
if socket.gethostname().endswith('.local'):
    from settings import develop as settings
else:
    from settings import staging as settings

MONGO_URI = settings.MONGO_URI
FILEFORMATS = settings.FILEFORMATS
POPULATION = 'unknown'  # FIXME


def glob_import(datadir, host=MONGO_URI):
    with pymongo.Connection(host=host) as connection:
        db = connection['pergenie']
        users = db['user_info'].find()
        usernames = set([user['user_id'] for user in users])

        for username in usernames:
            # Try to import/update files
            # If timestamp is newer than one in DB, re-import.
            for fileformat in FILEFORMATS:
                glob_path = os.path.join(datadir, username, fileformat[0], fileformat[1])
                filepaths = glob.glob(glob_path)

                for filepath in filepaths:
                    last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(filepath))
                    info = {'user_id': username,
                            'name': clean_file_name(os.path.basename(filepath)),
                            'raw_name': os.path.basename(filepath),
                            'date': last_modified,
                            'population': POPULATION,
                            'file_format': fileformat[0],
                            'catalog_cover_rate': db['catalog_cover_rate'].find_one({'stats': 'catalog_cover_rate'})['values'][fileformat[0]],
                            'genome_cover_rate': db['catalog_cover_rate'].find_one({'stats': 'genome_cover_rate'})['values'][fileformat[0]],
                            'status': float(0.0)}

                    db_info = db['data_info'].find_one({'user_id': username, 'raw_name': os.path.basename(filepath)})
                    if db_info and last_modified < db_info['date']: continue

                    print 'Importing into DB:', filepath
                    print import_variants(filepath,
                                          info['population'],
                                          info['file_format'],
                                          info['user_id'],
                                          settings)
                    db['data_info'].insert(info)

            # Try to delete non exist files.
            # If file exists in DB, but does not exist,
            # delete data_info and variants from DB.
            user_datas = db['data_info'].find({'user_id': username})
            for user_data in user_datas:
                db_filepath = os.path.join(datadir, username, user_data['file_format'], user_data['raw_name'])
                if not os.path.exists(db_filepath):
                    print 'Deleting from DB:', db_filepath,
                    db.drop_collection('variants.{0}.{1}'.format(username, clean_file_name(user_data['raw_name'])))
                    db.drop_collection('reports.{0}.{1}'.format(username, clean_file_name(user_data['raw_name'])))
                    for r in db['data_info'].find({'user_id': username, 'raw_name': user_data['raw_name']}):
                        db['data_info'].remove(r)


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument('datadir')
    args = parser.parse_args()

    glob_import(args.datadir)

if __name__ == '__main__':
    _main()
