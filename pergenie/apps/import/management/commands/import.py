# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from optparse import make_option
import unicodedata
import shout
import daemon
import daemon.pidfile
from signal import SIGTSTP, SIGABRT
import sys, os


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            "--gwascatalog",
            action="store_true",
            dest="gwascatalog",
            help="Import GWAS Catalog into database"
        ),
    )

    def handle(self, *args, **options):
        pidFile = os.path.dirname(
            os.path.abspath(__file__)
            ) + "/../../../daemon.pid"

        if options["gwascatalog"]:
            # if (options["host"] is None or
            #     options["port"] is None or
            #     options["password"] is None
            # ):
            #     print "Required arguments: host, port, password"
            #     self.print_help("jukebox_shout", "help")
            #     return

            # if os.path.exists(pidFile):
            #     print "Daemon already running, pid file exists"
            #     return

            pid = daemon.pidfile.TimeoutPIDLockFile(
                pidFile,
                10
            )

            self.shout = shout.Shout()
            print "Using libshout version %s" % shout.version()

            try:
                self.shout.open()
                self.shout.close()
            except shout.ShoutException as exception:
                print "Error: " + str(exception)
                return

            if options["fg"]:
               self.shout.open()

               print "Register player"
               pid = os.getpid()
               players_api = jukebox_core.api.players()
               players_api.add(pid)

               songs_api = jukebox_core.api.songs()
               while 1:
                   song = songs_api.getNextSong()
                   self.sendfile(song)

        else:
            self.print_help("jukebox_shout", "help")


    def shutdown(self, signal, action):
        self.shout.close()
        self.daemon.close()
        sys.exit(0)
