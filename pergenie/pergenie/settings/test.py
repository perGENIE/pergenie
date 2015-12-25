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
        'NAME': 'pergenie',
        'USER': 'pergenie',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    },
}


# Genome
UPLOAD_ROOT = os.path.join(BASE_DIR, 'tmp')
GENOME_UPLOAD_DIR = os.path.join(UPLOAD_ROOT, 'genome')

RS_MERGE_ARCH_PATH = os.path.join(BASE_DIR, 'test', 'data', 'RsMergeArch.bcp.gz')
