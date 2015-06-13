# coding: utf-8
from common import *

SECRET_KEY = 'secretkey_secretkey_secretkey_secretkey_secretkey_secretkey'
DEBUG = True


# Application definition

INSTALLED_APPS += (
    # 'debug_toolbar',
    'django_extensions',
)

MIDDLEWARE_CLASSES += (
    # 'debug_toolbar.middleware.DebugToolbarMiddleware',
)


# Email

SUPPORT_EMAIL = ''
NOREPLY_EMAIL = ''


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'db.sqlite3',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    },
}

# MongoDB
MONGO_HOST = "localhost"
MONGO_PORT = 27017
MONGO_USER = ""
MONGO_PASSWORD = ""
MONGO_URI = "mongodb://{HOST}:{PORT}".format(HOST=MONGO_HOST,
                                             PORT=MONGO_PORT)
# MONGO_URI = "mongodb://{USER}:{PASSWORD}@{HOST}:{PORT}".format(USER=MONGO_USER,
#                                                                PASSWORD=MONGO_PASSWORD,
#                                                                HOST=MONGO_HOST,
#                                                                PORT=MONGO_PORT)

# Celery (RabbitMQ)
BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "guest"
BROKER_PASSWORD = "guest"
BROKER_VHOST = "/"
CELERY_RESULT_BACKEND = "amqp"
CELERYD_LOG_FILE = "/tmp/celeryd.log"
CELERYD_LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR or CRITICAL