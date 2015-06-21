import os

from django.conf import settings

from celery.task import Task
from celery.decorators import task

from lib.mongo.import_genotypes import import_genotypes
from utils import clogging
log = clogging.getColorLogger(__name__)


@task
def import_genotypes(genome_id, file_path, file_format):
    logger = Task.get_logger()
    logger.info('Importing genotypes...')

    import_genotypes(genome_id, file_path, file_format)

    # TODO: Catch Exceptions
