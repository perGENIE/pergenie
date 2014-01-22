import sys, os
from pprint import pformat
from pymongo import MongoClient

from celery.task import Task
from celery.decorators import task
from mongo.import_variants import import_variants
from django.conf import settings
from lib.r.r import projection
from utils import clogging
log = clogging.getColorLogger(__name__)
from lib.api.riskreport import RiskReport
riskreport = RiskReport()

# ref: http://yuku-tech.hatenablog.com/entry/20101112/1289569700

@task
def add(x, y):
    logger = Task.get_logger()
    logger.info("Adding {0} + {1}".format(x, y))
    return x + y


@task
def qimport_variants(info):
    logger = Task.get_logger()
    logger.info('qimporting ...')
    logger.info(pformat(info))

    file_path = os.path.join(settings.UPLOAD_DIR,
                             info['user_id'],
                             info['file_format'],
                             info['raw_name'])
    log.info(import_variants(file_path,
                             info['population'],
                             info['file_format'],
                             info['user_id']))

    # if import_error_state:
    #     err = ', but import failed...' + import_error_state

    # os.remove(file_path)

    # Risk Report
    riskreport.import_riskreport(info)

    log.debug('write riskreport...')
    file_infos = genomes.get_data_infos(info['user_id'])
    riskreport.write_riskreport(info['user_id'], file_infos, force_uptade=True)

    # Population PCA
    person_xy = [0,0]  # projection(info)
    with MongoClient(host=settings.MONGO_URI) as connection:
        db = connection['pergenie']
        data_info = db['data_info']
        data_info.update({'user_id': info['user_id'], 'name': info['name']},
                         {"$set": {'pca': {'position': person_xy,
                                           'label': info['user_id'],
                                           'map_label': ''},
                                   'status': 100}})
