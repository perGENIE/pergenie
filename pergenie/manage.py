#!/usr/bin/env python
import sys, os
import getpass
import socket
import psutil
from lib.utils.service import is_up
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    log.info('appuser: {}'.format(getpass.getuser()))

    host = socket.gethostname()
    log.info('host: {}'.format(host))

    if host.endswith('.local'):
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pergenie.settings.develop")
    else:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pergenie.settings.staging")

    if not is_up('mongod'):
        log.critical("mongod is not alive")
        sys.exit()

    execute_from_command_line(sys.argv)
