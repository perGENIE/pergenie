# -*- coding: utf-8 -*-

from optparse import make_option

from termcolor import colored
from django.core.management.base import BaseCommand
from django.conf import settings

from lib.mongo.import_OMIM import OMIMParser
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            "--omim",
            action="store_true",
            dest="omim",
            help=colored("Import OMIM into database", "green")
        ),
    )

    def handle(self, *args, **options):
        if options["omim"]:
            log.info('Try to import omim ...')
            omim_parser = OMIMParser(settings)
            omim_parser.insert_to_mongo()
            omim_parser.check()
        else:
            self.print_help("import", "help")
