#!/home/w3pgenie/.virtualenvs/work/bin/python

import sys
import os

# Make sure to change 'username' to your username!
sys.path.append('/home/w3pgenie/.virtualenvs/work/lib/python2.7/site-packages')

os.environ['DJANGO_SETTINGS_MODULE'] = 'pergenie.settings'

from django.core.servers.fastcgi import runfastcgi
runfastcgi(method="threaded", daemonize="false")
