#!/usr/bin/env python
import sys, os
import getpass
import socket

if __name__ == "__main__":
    who_am_i = getpass.getuser()
    print 'i am', who_am_i

    host = socket.gethostname()
    print 'host: ', host

    if host.endswith('.local'):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pergenie.settings.develop")
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pergenie.settings.staging")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
