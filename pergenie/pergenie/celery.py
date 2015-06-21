from __future__ import absolute_import
import os
import socket

from django.conf import settings
from celery import Celery


# set the default Django settings module for the 'celery' program.
host = socket.gethostname()
if host.endswith('.local'):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pergenie.settings.development")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pergenie.settings.staging")

app = Celery('pergenie')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
