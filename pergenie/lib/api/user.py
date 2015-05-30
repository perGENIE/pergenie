import sys, os
import getpass
import socket
from pymongo import MongoClient
import lepl.apps.rfc3696
email_validator = lepl.apps.rfc3696.Email()
from django.contrib.auth.models import User as django_User
from django.utils.translation import ugettext as _
from django.core.mail import send_mail
from lib.common import clean_file_name
from django.conf import settings
from utils import clogging
log = clogging.getColorLogger(__name__)


class User(object):
    def create(self, user_id, password=None, account_activation=settings.ACCOUNT_ACTIVATION):
        if not password:
            password = getpass.getpass("Enter your password:")
            repassword = getpass.getpass("Retype your password:")
            if password != repassword:
                raise Exception(_('Passwords do not match.'))

        # Validations
        if len(password) < int(settings.MIN_PASSWORD_LENGTH):
            raise Exception(_('Passwords too short (passwords should be longer than %(min_password_length)s characters).' % {'min_password_length': settings.MIN_PASSWORD_LENGTH}))

        if not email_validator(user_id):
            raise Exception(_('Invalid mail address assumed.'))

        if any(x in user_id for x in set(settings.INVALID_USER_ID_CHARACTERS)):
            raise Exception(_('Invalid mail address assumed.'))

        if settings.ALLOWED_EMAIL_DOMAINS and not user_id.split('@')[-1] in settings.ALLOWED_EMAIL_DOMAINS:
            raise Exception(_('Invalid mail address assumed.'))
            log.warn('Attempt to register by not allowed email domain: %s' % user_id)
            send_mail(subject='warn',
                      message='Attempt to register by not allowed email domain: %s' % user_id,
                      from_email=settings.EMAIL_HOST_USER,
                      recipient_list=[settings.EMAIL_HOST_USER],
                      fail_silently=False)

        if user_id in settings.RESERVED_USER_ID:
            raise Exception(_('Already registered.'))

        if django_User.objects.filter(username=user_id):
            raise Exception(_('Already registered.'))

        user = django_User.objects.create_user(user_id, user_id, password)
        user.save()


    def delete(self, user_id):
        # Delete django User
        user = django_User.objects.filter(username=user_id)
        user.delete()

        # TODO:
        # Delete genome data in upload directory
        # Delete mongo.variants
        # Delete mongo.riskreport
