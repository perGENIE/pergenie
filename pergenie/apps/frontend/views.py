# -*- coding: utf-8 -*-

from django.contrib.sites.models import Site
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.shortcuts import redirect  # , render_to_response
# from django.template import RequestContext
from django.views.decorators.http import require_http_methods
from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template
from django.utils.translation import ugettext as _
from django.conf import settings

from django.db import IntegrityError
from django.http import Http404

import os
import pymongo

from apps.frontend.forms import LoginForm, RegisterForm
from django.forms import ValidationError

from utils import clogging
log = clogging.getColorLogger(__name__)


def index(request):
    return redirect('apps.frontend.views.login')


@require_http_methods(['GET', 'POST'])
def login(request):
    params = {'erorr': ''}

    if request.method == 'POST':
        while True:
            form = LoginForm(request.POST)

            if not form.is_valid():
                params['error'] = _('Invalid request.')
                break

            user = authenticate(username=form.cleaned_data['user_id'],
                                password=form.cleaned_data['password'])

            if user is None:
                params['error'] = _('invalid mail address or password')
                break

            if not user.is_active:
                params['error'] = _('invalid mail address or password')
                break

            auth_login(request, user)
            return redirect('apps.dashboard.views.index')

    return direct_to_template(request, 'login.html', params)


def logout(request):
    auth_logout(request)
    return redirect('apps.frontend.views.index')


@require_http_methods(['GET', 'POST'])
def register(request):
    params = {'is_succeeded': False,
              'error': '',
              'login_url': ''}

    if request.method == 'POST':
        while True:
            form = RegisterForm(request.POST)

            if not form.is_valid():
                params['error'] = _('Invalid request.')
                # contains `null input` case
                break

            user_id = form.cleaned_data['user_id']
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']

            # TODO: check if user_id is valid char. not ", ', \, ...

            if password1 != password2:
                params['error'] = _('Passwords do not match.')
                break

            if len(password1) < int(settings.MIN_PASSWORD_LENGTH):
                params['error'] = _('Passwords too short (passwords should be longer than %(min_password_length)s characters).' % {'min_password_length': settings.MIN_PASSWORD_LENGTH})
                break

            if user_id in settings.RESERVED_USER_ID:
                params['error'] = _('Already registered.')
                params['login_url'] = reverse('apps.frontend.views.login')
                log.debug('Reserved user_id')
                break

            try:
                user = User.objects.create_user(user_id, user_id, password1)
                user.save()
            except IntegrityError, e:
                # not unique user_id
                params['error'] = _('Already registered.')
                params['login_url'] = reverse('apps.frontend.views.login')
                log.debug('IntegrityError')
                break
            except:
                params['error'] = _('Unexpected error')
                log.error('Unexpected error: {}'.format(e))
                break

            params['is_succeeded'] = True
            # password = password1
            # _('You have successfully registered!')

            """
            * Simple registration (without mail verification)
            """
            if not settings.ACCOUNT_ACTIVATION:
                auth_login(request, user)
                return redirect('apps.dashboard.views.index')

            """
            * Registration with mail verification
            """
            with pymongo.Connection(port=settings.MONGO_PORT) as connection:
                db = connection['pergenie']
                user_info = db['user_info']

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
            activation_url = os.path.join(str(Site.objects.get_current()), 'activation', activation_key)
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
                return direct_to_template(request, 'registeration_completed.html')
            except:  # SMTPException:
                params['error'] = _('Invalid mail address assumed.')
                log.debug('mail failed')

                # send activation_key faild, so delete user
                user_info.remove({'user_id': user_id})
                user.delete()

                break

            break

    log.debug(params)
    return direct_to_template(request, 'register.html', params)


def activation(request, activation_key):
    """Activate user by activation key.
    """

    params = {'error':''}

    # find the user who has this activation key
    with pymongo.Connection(port=settings.MONGO_PORT) as connection:
        db = connection['pergenie']
        user_info = db['user_info']
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
                params['error'] = 'Activation successful, but failed to send you notification email...'
                log.error('Failed to send notification. {}'.format(challenging_user_info['user_id']))

            break

    return direct_to_template(request, 'activation_completed.html', params)
