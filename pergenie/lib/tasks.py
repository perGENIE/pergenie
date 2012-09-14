from celery.task import Task
from celery.decorators import task
import mongo.import_variants as import_variants

# ref: http://yuku-tech.hatenablog.com/entry/20101112/1289569700

# @task
# def add(x, y):
#     logger = Task.get_logger()
#     logger.info("Adding {0} + {1}".format(x, y))
# #     return x + y


@task
def qimport_variants(file_path, tmp_data_info):
    logger = Task.get_logger()
    logger.info('qimporting {0}, {1}'.format(file_path, tmp_data_info))

    import_error_state= import_variants.import_variants(file_path,
                                                        tmp_data_info['population'],
                                                        tmp_data_info['file_format'],
                                                        tmp_data_info['user_id'])
    
    if import_error_state:
        err = ', but import failed...' + import_error_state
        os.remove(file_path)  # ok?
