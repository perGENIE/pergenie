# -*- coding: utf-8 -*-

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

from django.core.mail import send_mail, BadHeaderError
from smtplib import SMTPException

import pymongo

from apps.frontend.forms import LoginForm, RegisterForm

from utils import clogging
log = clogging.getColorLogger(__name__)

# import pymongo


class ReservedUserIDError(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        # return repr(self.value)
        return str(self.value)


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
              'has_error': False,
              'message': ''}

    if request.method == 'POST':
        form = RegisterForm(request.POST)

        if form.is_valid():
            user_id = form.cleaned_data['user_id']
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']

            # TODO: validate email is name@example.com

            if password1 == password2:
                try:
                    # check if user_id is not RESERVED_ID like 'test'
                    if user_id in settings.RESERVED_USER_ID:
                        raise ReservedUserIDError, '"{}" is RESERVED_ID'.format(user_id)

                    #TODO: check if user_id is valid char. not ", ', \, ...
                    #
                    #

                    user = User.objects.create_user(user_id, user_id, password1)
                    user.save()

                except IntegrityError, e:
                    # not unique user_id
                    params['has_error'] = True
                    params['message'] = _('Already registered.') + ' <a href="{}">login</a>'.format(reverse('apps.frontend.views.login'))
                    log.error('IntegrityError: {}'.format(e))

                except ReservedUserIDError, e:
                    # user_id is reserved user_id
                    params['has_error'] = True
                    params['message'] = _('Already registered.') + ' <a href="{}">login</a>'.format(reverse('apps.frontend.views.login'))
                    log.error('ReservedUserIDError: {}'.format(e))

                except:
                    #
                    params['has_error'] = True
                    params['message'] = _('Unexpected error.')

                else:
                    params['is_succeeded'] = True
                    password = password1
                    params['message'] = _('You have successfully registered!')

            else:
                params['has_error'] = True
                params['message'] = _('Passwords do not match.')


        else:
            params['has_error'] = True
            params['message'] = _('Invalid request.')
            # contains null password


    if params['is_succeeded']:
        # ?
#         user = authenticate(username=user_id,
#                             password=password)

        """
        Registration with e-mail validation
        """

        if user:
            if not settings.ACCOUNT_ACTIVATION:
                auth_login(request, user)
                return redirect('apps.dashboard.views.index')

            else:
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

                log.debug(user_info.find({'user_id': user_id}))

                # Deactivate user activation
                user.is_active = False
                user.save()

                # Send a mail with activation_key to user
                email_title = "Welcome to perGENIE"
                email_body = """
to activate and use your account, click the link below or copy and paste it into your web browser's address bar
%(activation_key)s
""" % {'activation_key': activation_key}

                try:
                    user.email_user(subject=email_title,
                                    message=email_body)
                except SMTPException:
                    log.error('invalid email-address assumed')
                except:
                    log.error('invalid email-address assumed')

                # TODO: not redirect to login, but redirect to register_completed
                #       or show message: 'Please check email ...'
                # return direct_to_template(request, 'login.html')

            #     return redirect('apps.frontend.views.register_completed')
                msgs = {}
                return direct_to_template(request, 'register_completed.html', msgs)

        else:
            # which case ?
            params['error'] = _('Invalid mail address or password.')

    else:
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
