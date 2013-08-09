import sys, os
import getpass
import socket
from pymongo import MongoClient
import lepl.apps.rfc3696
email_validator = lepl.apps.rfc3696.Email()
from django.contrib.auth.models import User as django_User
from django.utils.translation import ugettext as _
from django.core.mail import send_mail
from django.conf import settings
from utils import clogging
log = clogging.getColorLogger(__name__)


class User(object):
    def __init__(self):
        pass

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

        user = django_User.objects.create_user(user_id, '', password)

        for fileformat in settings.FILEFORMATS:
            tmp_upload_dir = os.path.join(settings.UPLOAD_DIR, user_id, fileformat[0])
            if not os.path.exists(tmp_upload_dir):
                os.makedirs(tmp_upload_dir)
                os.chmod(tmp_upload_dir, 777)  # FIXME: how do we deal directory ownership

        # TODO: move to mysql
        # create user_info
        with MongoClient(host=settings.MONGO_URI) as c:
            user_info = c['pergenie']['user_info']

            # Ensure old one does not exist
            if user_info.find_one({'user_id': user_id}): user_info.remove({'user_id': user_id})

            user_info.insert({'user_id': user_id,
                              'risk_report_show_level': 'show_all',
                              'activation_key': ''})

            if account_activation:
                # Generate unique activation_key
                while True:
                    activation_key = django_User.objects.make_random_password(length=settings.ACCOUNT_ACTIVATION_KEY_LENGTH)
                    if not user_info.find_one({'activation_key': activation_key}): break

                # add activation_key info to mongodb.user_info
                user_info.update({'user_id': user_id},
                                 {"$set": {'activation_key': activation_key}},
                                 upsert=True)

                # Deactivate user activation
                user.is_active = False

        user.save()


    def send_activation_email(self, user_id):
        with MongoClient(host=settings.MONGO_URI) as c:
            user_info = c['pergenie']['user_info']
            tmp_user_info = user_info.find_one({'user_id': user_id})
            if tmp_user_info:
                activation_key = tmp_user_info['activation_key']
            else:
                log.error('Such user does not exist: %s' % user_id)
                raise Exception(_('Such user does not exist.'))

        # Send email with activation_key
        hostname = socket.gethostname()
        activation_url_base = 'http://' + hostname
        activation_url = os.path.join(activation_url_base, 'activation', activation_key)
        if not activation_url.endswith(os.path.sep):
            activation_url += os.path.sep

        email_title = "Welcome to perGENIE"
        email_body = """Welcome to perGENIE!

To complete your registration, please visit following URL:

%(activation_url)s

If you have problems with signing up, please contact us at %(support_email)s


- perGENIE teams

--
This email address is SEND ONLY, NO-REPLY.
""" % {'activation_url': activation_url, 'support_email': settings.SUPPORT_EMAIL}

        try:
            user.email_user(subject=email_title, message=email_body)
        except:  # SMTPException
            # Send activation_key faild, so delete user
            with MongoClient(host=settings.MONGO_URI) as c:
                user_info = c['pergenie']['user_info']
                user_info.remove({'user_id': user_id})
            user = django_User.objects.filter(username=user_id)
            user.delete()
            log.error('send activaton email failed')
            raise Exception(_('Invalid mail address assumed.'))


    def activate(self):
        with MongoClient(host=settings.MONGO_URI) as c:
            user_info = c['pergenie']['user_info']

            # Find the user who has this activation key
            challenging_user_info = user_info.find_one({'activation_key': activation_key})
            if not challenging_user_info:
                raise Exception('Invalid activation_key')

            challenging_user = django_User.objects.get(username__exact=challenging_user_info['user_id'])
            if challenging_user.is_active:
                raise Exception('Already activated')

            # Activate
            challenging_user.is_active = True
            challenging_user.save()

            # Delete activation_key in mongodb
            user_info.update({'user_id': challenging_user_info['user_id']},
                             {"$set": {'activation_key': ''}})

            # Send email notification that 'your account has been activated.'
            try:
                challenging_user.email_user(subject='Your account has been activated',
                                            message="""Your perGENIE account has been activated!

If this account activation is not intended by you, please contact us at %(support_email)s


- perGENIE teams

--
This email address is SEND ONLY, NO-REPLY.
"""  % {'support_email': settings.SUPPORT_EMAIL})
            except:
                log.error('Failed to send notification. %s' % challenging_user_info['user_id'])


    def delete(self, user_id):
        # Delete django User
        user = django_User.objects.filter(username=user_id)
        user.delete()

        # Delete user_info
        with MongoClient(host=settings.MONGO_URI) as c:
            user_info = c['pergenie']['user_info']
            user_info.remove({'user_id': user_id})

        # TODO:
        # Delete genome data in upload directory
        # Delete mongo.variants
        # Delete mongo.riskreport
