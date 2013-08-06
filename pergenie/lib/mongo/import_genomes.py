# -*- coding: utf-8 -*-

import sys, os
import glob
import datetime
import pymongo
from lib.common import clean_file_name
from lib.mongo.import_variants import import_variants
from utils import clogging
log = clogging.getColorLogger(__name__)


def import_genomes(settings):
    """
    This script will be used as cron job:

    ```
    $ python manage.py import --genomes
    ```

    Suppose genome files are stored in `/somewhere/fileformat/genomedata.ext`.
    Cron target dirs are specified in settings as follows:

    ```
    CRON_DIRS = {'username':  ['/somewhere'], ...}
    ```


    NOTES
    -----

    * Check time-stamps to determine update or not.
    * If file is multi sample vcf, only 1st sample will be imported.


    TODO
    ----

    * support multi sample vcf

    """

    POPULATION = settings.DEFAULT_POPULATION  # FIXME

    with pymongo.Connection(host=settings.MONGO_URI) as connection:
        db = connection['pergenie']
        users = db['user_info'].find()
        usernames = set([user['user_id'] for user in users])

        for username in settings.CRON_DIRS.keys():
            log.debug(username)
            # Try to import/update files
            # If timestamp is newer than one in DB, re-import.
            for datadir in settings.CRON_DIRS[username]:
                for fileformat in settings.FILEFORMATS:
                    glob_path = os.path.join(datadir, fileformat[0], fileformat[1])
                    filepaths = glob.glob(glob_path)

                    for filepath in filepaths:
                        log.debug(filepath)
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

                        log.info('Importing into DB: %s' % filepath)
                        log.info(import_variants(filepath,
                                                 info['population'],
                                                 info['file_format'],
                                                 info['user_id'],
                                                 settings))
                        # population PCA
                        person_xy = [0,0]  # FIXME: projection(info)
                        db['data_info'].update({'user_id': info['user_id'], 'raw_name': info['raw_name']},
                                               {"$set": {'pca': {'position': person_xy,
                                                                 'label': info['user_id'],
                                                                 'map_label': ''},
                                                         'status': 100}})
                        db['data_info'].insert(info)


            # Try to delete non exist files.
            # If file exists in DB, but does not exist,
            # delete data_info and variants from DB.
            user_datas = db['data_info'].find({'user_id': username})
            for user_data in user_datas:
                db_filepath = os.path.join(datadir, user_data['file_format'], user_data['raw_name'])
                if not os.path.exists(db_filepath):
                    log.warn('Deleting from DB: %s' % db_filepath)
                    db.drop_collection('variants.{0}.{1}'.format(username, clean_file_name(user_data['raw_name'])))
                    db.drop_collection('reports.{0}.{1}'.format(username, clean_file_name(user_data['raw_name'])))
                    for r in db['data_info'].find({'user_id': username, 'raw_name': user_data['raw_name']}):
                        db['data_info'].remove(r)
