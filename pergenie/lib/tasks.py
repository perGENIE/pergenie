from celery.task import Task
from celery.decorators import task
import mongo.import_variants as import_variants

from pprint import pformat

import os
UPLOAD_DIR = '/tmp/pergenie'

# ref: http://yuku-tech.hatenablog.com/entry/20101112/1289569700

# @task
# def add(x, y):
#     logger = Task.get_logger()
#     logger.info("Adding {0} + {1}".format(x, y))
# #     return x + y


@task
def qimport_variants(data_info):
    logger = Task.get_logger()
    logger.info('qimporting ...')
    logger.info(pformat(data_info))

    import_error_state= import_variants.import_variants(data_info['name'],
                                                        data_info['population'],
                                                        data_info['file_format'],
                                                        data_info['user_id'])
    
    if import_error_state:
        err = ', but import failed...' + import_error_state
        os.remove(os.path.join(UPLOAD_DIR, data_info['user_id'], data_info['name']))  # ok?
