# -*- coding: utf-8 -*-

import sys, os
import glob
import shutil
from pprint import pprint
from optparse import make_option

from pymongo import MongoClient
# from termcolor import colored
from django.core.management.base import BaseCommand
from django.conf import settings
from lib.api.genomes import Genomes
genomes = Genomes()
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            "--variants",
            action='store_true',
            help=""
        ),
        make_option(
            "--reports",
            action='store_true',
            help=""
        ),
        make_option(
            "--user",
            action='store_true',
            help=""
        ),
    )

    def handle(self, *args, **options):
        if not args:
            self.print_help("drop", "help")
            return

        log.info('Drop collections...')

        with MongoClient(host=settings.MONGO_URI) as c:
            db = c['pergenie']
            data_info = db['data_info']

            if options["variants"]:
                # Drop collection `variants.file_uuid`
                targets = []
                for user_id in args:
                    targets += genomes.get_all_variants(user_id)

                pprint(targets)
                print '...will be deleted'
                yn = raw_input('y/n > ')
                if yn == 'y':
                    for target in targets:
                        db.drop_collection(target)

                # Drop document in `data_info`
                targets = []
                for user_id in args:
                    targets += list(data_info.find({'user_id': user_id}))

                pprint(targets)
                print '...will be deleted'
                yn = raw_input('y/n > ')
                if yn == 'y':
                    for target in targets:
                        data_info.remove(target)

            if options["reports"]:
                print 'sorry, not implemented yet...'
                return

            if options["user"]:
                print 'sorry, not implemented yet...'
                return

                # Remove record in Django Database
                # TODO:


                # Drop document in `user_info`
                # TODO:


                # rm `dir`
                targets = []
                for user_id in args:
                    targets += glob.glob(os.path.join(settings.UPLOAD_DIR, user_id))  # FIXME: use UUID ?

                pprint(targets)
                print '...will be deleted'
                yn = raw_input('y/n > ')
                if yn == 'y':
                    for target in targets:
                        shutil.rmtree(target) # rm -r <dir>
