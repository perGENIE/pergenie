# -*- coding: utf-8 -*-

from django.contrib.sites.models import Site
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.shortcuts import redirect  # , render_to_response
# from django.template import RequestContext
from django.views.decorators.http import require_http_methods
from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template
# from django.utils import translation
from django.utils.translation import ugettext as _
from django.conf import settings

from django.db import IntegrityError

# from django.core.mail import send_mail, BadHeaderError
from smtplib import SMTPException

import os
import pymongo

from apps.frontend.forms import LoginForm, RegisterForm

from utils import clogging
log = clogging.getColorLogger(__name__)


def index(request):
    return redirect('apps.frontend.views.login')


@require_http_methods(['GET', 'POST'])
def login(request):
    params = {'erorr': ''}

    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            user = authenticate(username=form.cleaned_data['user_id'],
                                password=form.cleaned_data['password'])

            if user:
                auth_login(request, user)
                return redirect('apps.dashboard.views.index')

            else:
                params['error'] = _('invalid mail address or password')

        else:
            params['error'] = _('Invalid request.')

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
            # Generate activation_key
            activation_key = User.objects.make_random_password(length=settings.ACCOUNT_ACTIVATION_KEY_LENGTH)

            # add activation_key info to mongodb.user_info
            with pymongo.Connection(port=settings.MONGO_PORT) as connection:
                db = connection['pergenie']
                user_info = db['user_info']

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
            email_body = """
to activate and use your account, click the link below or copy and paste it into your web browser's address bar
%(activation_url)s
""" % {'activation_url': activation_url}

            log.debug('try mail')
            try:
                user.email_user(subject=email_title,
                                message=email_body)
                log.debug('mail sent')
                log.debug(params)
                return direct_to_template(request, 'register_completed.html')
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

    msgs = {}

    # TODO: if incorrect activation_key, 404?
    #       or, in urls.py, [a-z][]...{length} only accepts

    # find the user who has this activation key
    with pymongo.Connection(port=settings.MONGO_PORT) as connection:
        db = connection['pergenie']
        user_info = db['user_info']
        challenging_user_info = user_info.find_one({'activation_key': activation_key})

        # TODO: verify this user_id is unique
        # activate
        if challenging_user_info:
            challenging_user = User.objects.get(username__exact=challenging_user_info['user_id'])
            challenging_user.is_active = True
            challenging_user.save()

            # TODO: send a mail to user? 'your account has been activated.'

    return direct_to_template(request, 'activation_completed.html', msgs)
