from django.contrib.auth.models import User
from django.conf import settings

import sys, os
import datetime
from pymongo import MongoClient
from lib.common import clean_file_name
from lib.mongo.import_variants import import_variants
from utils import clogging
log = clogging.getColorLogger(__name__)


def _create_demo_user():
    # create user
    User.objects.create_user(settings.DEMO_USER_ID,
                             '',
                             settings.DEMO_USER_ID)

    # no need to make directory for upload, because we will import stored data.

    # create user_info
    with MongoClient(port=settings.MONGO_PORT) as c:
        user_info = c['pergenie']['user_info']
        user_info.insert({'user_id': settings.DEMO_USER_ID,
                          'risk_report_show_level': 'show_all',
                          'activation_key': ''})


def _import_demo_genome():
    targets = [settings.DEMO_23ANDME_GENOME_EU_M,
               settings.DEMO_23ANDME_GENOME_EU_F]  # ,
               # settings.TOMITA_GENOME]

    for target in targets:
        if os.path.exists(target['name']):
            log.debug('demo data exists {}'.format(target['name']))

            with MongoClient(port=settings.MONGO_PORT) as c:
                catalog_cover_rate = c['pergenie']['catalog_cover_rate']
                info = {'user_id': settings.DEMO_USER_ID,
                        'name': clean_file_name(os.path.basename(target['name'])),
                        'raw_name': os.path.basename(target['name']),
                        'date': datetime.datetime.today(),
                        'population': target['population'],
                        'file_format': target['file_format'],
                        'catalog_cover_rate': catalog_cover_rate.find_one({'stats': 'catalog_cover_rate'})['values'][target['file_format']],
                        'genome_cover_rate': catalog_cover_rate.find_one({'stats': 'genome_cover_rate'})['values'][target['file_format']],
                        'status': float(0.0)}

                data_info = c['pergenie']['data_info']
                data_info.insert(info)

                log.debug('importing genome for demo...')
                import_variants(file_path=target['name'],
                                population=target['population'],
                                file_format=target['file_format'],
                                user_id=settings.DEMO_USER_ID)


def init_demo_user():
    _create_demo_user()
    _import_demo_genome()
