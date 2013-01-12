# -*- coding: utf-8 -*- 

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_http_methods
from django.core.urlresolvers import reverse
from django.views.generic.simple import direct_to_template
from django.utils import translation
from django.utils.translation import ugettext as _
from django.conf import settings

from django.db import IntegrityError

from smtplib import SMTPRecipientsRefused

from apps.frontend.forms import LoginForm, RegisterForm

from utils import clogging
log = clogging.getColorLogger(__name__)

import pymongo

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
                    # params['message'] = _('You have successfully registered!')

            else:
                params['has_error'] = True
                params['message'] = _('Passwords do not match.')


        else:
            params['has_error'] = True
            params['message'] = _('Invalid request.')
            # contains null password


    if params['is_succeeded']:
        # verbose ?
        user = authenticate(username=user_id,
                            password=password)

        if user:
            # auth_login(request, user)
            # return redirect('apps.dashboard.views.index')
            try:
                user.email_user('welcome', 'hello world')
            except SMTPRecipientsRefused:
                log.error('invalid email-address assumed')
            except:
                log.error('unecpected emaiil_user error')
                
            # TODO: not redirect to login, but redirect to register_completed
            #       or show message: 'Please check email ...'
            return direct_to_template(request, 'login.html')

        else:
            params['error'] = _('Invalid mail address or password.')

    else:
        return direct_to_template(request, 'register.html', params)
