# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from optparse import make_option

from signal import SIGTSTP, SIGABRT
import sys, os

from termcolor import colored

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            "--gwascatalog",
            action="store_true",
            dest="gwascatalog",
            help=colored("Import GWAS Catalog into database", "green")
        ),
    )

    def handle(self, *args, **options):
        if options["gwascatalog"]:
            # try:
            #     self.shout.open()
            #     self.shout.close()
            # except shout.ShoutException as exception:
            #     print "Error: " + str(exception)
            #     return

            self.stdout.write("hello\n")
            

        else:
            self.print_help("import", "help")
