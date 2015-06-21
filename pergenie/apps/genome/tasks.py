# import sys
# import os
# from pprint import pformat

# from pymongo import MongoClient
# from pymongo_genomes import import_genome
from celery.task import Task
from celery.decorators import task
# from django.conf import settings

# from mongo.import_variants import import_variants
# from lib.r.r import projection
# from utils import clogging
# log = clogging.getColorLogger(__name__)
# from lib.api.riskreport import RiskReport
# riskreport = RiskReport()

# ref: http://yuku-tech.hatenablog.com/entry/20101112/1289569700

@task
def ping():
    return 'pong'


# @task
# def qimport_variants(info):
#     logger = Task.get_logger()
#     logger.info('qimporting ...')
#     logger.info(pformat(info))

#     file_path = os.path.join(settings.UPLOAD_DIR, info['owner'], info['file_name'])

#     import_genome(file_path,
#                   owner=info['owner'],
#                   file_format=info['file_format'],
#                   mongo_uri=settings.MONGO_URI)

#     # TODO:
#     # Risk Report
#     # riskreport.import_riskreport(info)

#     # log.debug('write riskreport...')
#     # file_infos = genomes.get_data_infos(info['user_id'])
#     # riskreport.write_riskreport(info['user_id'], file_infos, force_uptade=True)

#     # TODO: Catch Exceptions
#     # os.remove(file_path)
