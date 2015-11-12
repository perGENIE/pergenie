# coding: utf-8
from common import *

SECRET_KEY = 'secretkey_secretkey_secretkey_secretkey_secretkey_secretkey'


# Email

SUPPORT_EMAIL = ''
NOREPLY_EMAIL = ''
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = 'tmp/email'

# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ['DB_NAME'],
        'USER': os.environ['DB_USER'],
        'HOST': '127.0.0.1',
        'PORT': '5432',
    },
}
