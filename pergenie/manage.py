#!/usr/bin/env python
import sys, os
import getpass

if __name__ == "__main__":
    who_am_i = getpass.getuser()
    print 'i am', who_am_i

    if who_am_i == 'w3pgenie' or 'root':
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pergenie.settings.staging")
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pergenie.settings.develop")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
