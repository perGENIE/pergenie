# -*- coding: utf-8 -*-

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.shortcuts import redirect  # , render_to_response
# from django.template import RequestContext
from django.views.decorators.http import require_http_methods
from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template
# from django.utils import translation
from django.utils.translation import ugettext as _
from django.conf import settings
from django.db import IntegrityError
from django.http import Http404
from apps.frontend.forms import LoginForm, RegisterForm

import sys, os
from smtplib import SMTPRecipientsRefused
from pymongo import MongoClient
import lepl.apps.rfc3696
email_validator = lepl.apps.rfc3696.Email()

from demo import init_demo_user
from utils import clogging
log = clogging.getColorLogger(__name__)


def index(request):
    return direct_to_template(request, 'frontend/index.html')


def trydemo(request):
    """Login as DEMO USER (demo@pergenie.org)"""

    if not User.objects.filter(username=settings.DEMO_USER_ID):
        init_demo_user()

    user = authenticate(username=settings.DEMO_USER_ID,
                        password=settings.DEMO_USER_ID)
    auth_login(request, user)
    return redirect('apps.dashboard.views.index')


@require_http_methods(['GET', 'POST'])
def login(request):
    err = ''

    if request.method == 'POST':
        while True:
            form = LoginForm(request.POST)

            if not form.is_valid():
                err = _('Invalid request.')
                break

            user_id = form.cleaned_data['user_id']
            password = form.cleaned_data['password']

            # if user_id in settings.RESERVED_USER_ID:
            #     err = _('invalid mail address or password')
            #     break

            user = authenticate(username=user_id, password=password)

            if user is None:
                err = _('invalid mail address or password')
                break

            if not user.is_active:
                # err = _('invalid mail address or password')
                err = _('invalid mail address or password')

                break

            auth_login(request, user)
            return redirect('apps.dashboard.views.index')

    return direct_to_template(request, 'frontend/login.html', dict(err=err))


def logout(request):
    auth_logout(request)
    return redirect('apps.frontend.views.login')


@require_http_methods(['GET', 'POST'])
def register(request):
    params = {'is_succeeded': False,
              'err': '',
              'login_url': ''}

    if request.method == 'POST':
        while True:
            form = RegisterForm(request.POST)

            if not form.is_valid():
                params['err'] = _('Invalid request.')  # contains case for null input
                break

            user_id = form.cleaned_data['user_id']
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']

            # TODO: check if user_id is valid char. not ", ', \, ...

            if password1 != password2:
                params['err'] = _('Passwords do not match.')
                break

            if len(password1) < int(settings.MIN_PASSWORD_LENGTH):
                params['err'] = _('Passwords too short (passwords should be longer than %(min_password_length)s characters).' % {'min_password_length': settings.MIN_PASSWORD_LENGTH})
                break

            if not email_validator(user_id):
                params['err'] = _('Invalid mail address assumed.')
                break

            if user_id in settings.RESERVED_USER_ID:
                params['err'] = _('Already registered.')
                params['login_url'] = reverse('apps.frontend.views.login')
                log.debug('Reserved user_id')
                break

            try:
                user = User.objects.create_user(user_id, user_id, password1)
                user.save()
            except IntegrityError, e:
                # if not unique user_id
                params['err'] = _('Already registered.')
                params['login_url'] = reverse('apps.frontend.views.login')
                log.debug('IntegrityError')
                break
            except:
                params['err'] = _('Unexpected error')
                log.error('Unexpected error: {}'.format(e))
                break

            params['is_succeeded'] = True
            # password = password1
            # _('You have successfully registered!')

            """
            Registration *without* mail verification
            """
            if not settings.ACCOUNT_ACTIVATION:
                auth_login(request, user)
                return redirect('apps.dashboard.views.index')

            """
            Registration *with* mail verification
            """
            with MongoClient(port=settings.MONGO_PORT) as c:
                user_info = c['pergenie']['user_info']

                # Generate unique activation_key
                while True:
                    activation_key = User.objects.make_random_password(length=settings.ACCOUNT_ACTIVATION_KEY_LENGTH)
                    if not user_info.find_one({'activation_key': activation_key}):
                        break

                # add activation_key info to mongodb.user_info
                # TODO: verify this user_id is unique
                user_info.update({'user_id': user_id},
                                 {"$set": {'risk_report_show_level': 'show_all',
                                           'activation_key': activation_key}},
                                 upsert=True)

                log.debug(list(user_info.find({'user_id': user_id})))

            # Deactivate user activation
            user.is_active = False
            user.save()

            # Send a mail with activation_key to user
            email_title = "Welcome to perGENIE"

            if os.environ['DJANGO_SETTINGS_MODULE'] == 'pergenie.settings.develop':
                activation_url_base = 'http://localhost:8080/'
            elif os.environ['DJANGO_SETTINGS_MODULE'] == 'pergenie.settings.staging':
                activation_url_base = 'http://http://172.16.2.100/'
                # activation_url_base = str(Site.objects.get_current())

            activation_url = os.path.join(activation_url_base, 'activation', activation_key)
            if not activation_url.endswith(os.path.sep):
                activation_url += os.path.sep
            email_body = """Welcome to perGENIE!

To complete your registration, please visit this URL:

%(activation_url)s

If you have problems with signing up, please contact us at %(support_email)s


perGENIE teams

--
This email address is SEND ONLY, NO-REPLY.
""" % {'activation_url': activation_url, 'support_email': settings.SUPPORT_EMAIL}

            log.debug('try mail')
            try:
                user.email_user(subject=email_title,
                                message=email_body)
                log.debug('mail sent')
                log.debug(params)
                params.update(dict(user_id=user_id))
                return direct_to_template(request, 'frontend/registration_completed.html')
            except:  # SMTPException:
                params['err'] = _('Invalid mail address assumed.')
                log.debug('mail failed')

                # send activation_key faild, so delete user
                user_info.remove({'user_id': user_id})
                user.delete()

                break

            break

    log.debug(params)
    return direct_to_template(request, 'frontend/register.html', params)


def activation(request, activation_key):
    """Activate user when accessed with correct activation key."""

    err = ''

    # find the user who has this activation key
    with MongoClient(port=settings.MONGO_PORT) as c:
        user_info = c['pergenie']['user_info']
        challenging_user_info = user_info.find_one({'activation_key': activation_key})

        while True:
            if activation_key == '':  # no need?
                raise Http404

            if not challenging_user_info:
                # invalid activation_key
                raise Http404

            challenging_user = User.objects.get(username__exact=challenging_user_info['user_id'])

            if challenging_user.is_active:  # no need?
                # already activated
                raise Http404

            # activate
            challenging_user.is_active = True
            challenging_user.save()

            # delete activation_key in mongodb
            user_info.update({'user_id': challenging_user_info['user_id']},
                             {"$set": {'activation_key': ''}})

            # send user a mail notification that 'your account has been activated.'
            try:
                challenging_user.email_user(subject='Your account has been activated',
                                            message="""Your account has been activated!

If this account activation is not intended by you, ....

perGENIE teams

--
This email address is SEND ONLY, NO-REPLY.
""")
            except:  # smtplib.SMTPException
                err = 'Activation successful, but failed to send you notification email...'
                log.error('Failed to send notification. {}'.format(challenging_user_info['user_id']))

            break

    return direct_to_template(request, 'frontend/activation_completed.html', dict(err=err))
