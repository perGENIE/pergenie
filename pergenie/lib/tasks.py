from celery.task import Task
from celery.decorators import task

@task
def add(x, y):
    logger = Task.get_logger()
    logger.info("Adding {0} + {1}".format(x, y))
    return x + y

