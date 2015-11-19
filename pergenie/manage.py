#!/usr/bin/env python
import sys
import os
import getpass
import socket
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    log.info('app_user: {}'.format(getpass.getuser()))

    host = socket.gethostname()
    log.info('host: {}'.format(host))

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pergenie.settings.development")

    execute_from_command_line(sys.argv)
