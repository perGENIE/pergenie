# coding: utf-8

import sys
import os
import socket

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(os.path.join(BASE_DIR, 'lib'))

DOMAIN = socket.gethostname()


# Application definition

DEFAULT_APPS = (
    'apps.application',
    'apps.authentication',
    'apps.dashboard',
    'apps.genome',
    'apps.snp',
    'apps.gwascatalog',
    'apps.riskreport',
    'apps.faq'
)

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
) + DEFAULT_APPS

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'pergenie.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'pergenie.wsgi.application'

SITE_ID = 1  # the current site in the django_site database table


# Session

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_SAVE_EVERY_REQUEST = True  # Default: False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    },
}


# Celery
BROKER_URL = 'amqp://{USER}:{PASSWORD}@{HOST}:{PORT}//'.format(USER='guest',
                                                               PASSWORD='guest',
                                                               HOST='localhost',
                                                               PORT=5672)
CELERY_RESULT_BACKEND = 'amqp'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'


# Internationalization

LANGUAGE_CODE = 'en'  # 'ja'

TIME_ZONE = 'Asia/Tokyo'

USE_I18N = True  # load the internationalization machinery
USE_L10N = True  # format dates, numbers and calendars according to the current locale
USE_TZ = True    # use timezone-aware datetimes

LANGUAGES = (
    ('en', u'English'),
    ('ja', u'日本語'),
)


# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'  # URL prefix for static files.

STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)


# Logging

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


# Authentication

AUTH_USER_MODEL = 'authentication.User'
LOGIN_URL = '/login/'
MIN_PASSWORD_LENGTH = 14

ACCOUNT_ACTIVATION_KYE_EXPIRE_HOURS= 24
ACCOUNT_ACTIVATION_KEY_LENGTH = 40


# Test

TEST_DATA_DIR = os.path.join(BASE_DIR, 'test', 'data')


# Application settings


# Genome upload/delete/status

MAX_UPLOAD_GENOME_FILE_NAME_LENGTH = 255
MAX_UPLOAD_GENOME_FILE_SIZE = 2 * (1024 ** 3)  # == 2Gbytes. 100Mbytes: 1024**2 == 104857600, 1Gbytes: 1024**3
MAX_UPLOAD_GENOMEFILE_COUNT = {
    'default': 3,
    'demo': 0
}

# GWAS Catalog

GWASCATALOG_URL = 'http://www.genome.gov/admin/gwascatalog.txt'
