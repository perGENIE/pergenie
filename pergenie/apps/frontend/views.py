import sys, os
from pymongo import MongoClient
from uuid import uuid4
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template
from django.utils.translation import ugettext as _
from django.conf import settings
from django.db import IntegrityError
from django.http import Http404
from django.core.mail import send_mail
from apps.frontend.forms import LoginForm, RegisterForm
from lib.api.user import User as pergenie_User
from utils import clogging
log = clogging.getColorLogger(__name__)


def index(request):
    return direct_to_template(request, 'frontend/index.html', dict(is_registerable=settings.IS_REGISTERABLE))


@require_http_methods(['GET', 'POST'])
def register(request):
    auth_logout(request)
    err = ''

    if request.method == 'POST':
        while True:
            form = RegisterForm(request.POST)

            if not form.is_valid():
                err = _('Invalid request.')  # contains case for null input
                break

            user_id = form.cleaned_data['user_id']
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']

            if password1 != password2:
                err = _('Passwords do not match.')
                break

            u = pergenie_User()
            try:
                u.create(user_id, password1)
            except Exception, e:
                err = str(e)
                break

            # Registration *without* mail verification
            if not settings.ACCOUNT_ACTIVATION:
                user = User.objects.filter(username=user_id)
                auth_login(request, user)
                return redirect('apps.dashboard.views.index')

            try:
                u.send_activation_email(user_id)
            except Exception, e:
                err = str(e)
                break

            return direct_to_template(request, 'frontend/registration_completed.html', dict(err=err, user_id=user_id))

    return direct_to_template(request, 'frontend/register.html', dict(err=err))


def activation(request, activation_key):
    u = pergenie_User()
    try:
        u.activate(activation_key)
    except Exception, e:
        log.error(e)
        raise Http404

    return direct_to_template(request, 'frontend/activation_completed.html')


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

            if settings.ALLOWED_EMAIL_DOMAINS and not user_id.split('@')[-1] in settings.ALLOWED_EMAIL_DOMAINS:
                err = _('invalid mail address or password')
                log.warn('Attempt to login by not allowed email domain: %s' % user_id)
                send_mail(subject='warn',
                          message='Attempt to login by not allowed email domain: %s' % user_id,
                          from_email=settings.EMAIL_HOST_USER,
                          recipient_list=[settings.EMAIL_HOST_USER],
                          fail_silently=False)
                break

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

            # # Remember Me
            # if not request.POST.get('remember_me', None):
            #     request.session.set_expiry(0)
            #     log.debug("Not Remember Me")

            # log.debug(request.session.get_expiry_age())

            return redirect('apps.dashboard.views.index')

    return direct_to_template(request, 'frontend/login.html', dict(err=err,
                                                                   is_registerable=settings.IS_REGISTERABLE))


def logout(request):
    auth_logout(request)
    return redirect('apps.frontend.views.login')


def trydemo(request):
    """Login as DEMO USER (demo@pergenie.org)
    """

    while True:
        try:
            demo_user_uid = settings.DEMO_USER_ID + '+' + str(uuid4())
            user = User.objects.create_user(demo_user_uid, '', settings.DEMO_USER_ID)
            user.save()
            break
        except IntegrityError, e:
            pass
        except:
            return direct_to_template(request, 'frontend/index.html')

    # create user_info
    with MongoClient(host=settings.MONGO_URI) as c:
        user_info = c['pergenie']['user_info']

        user_info.insert({'user_id': demo_user_uid,
                          'risk_report_show_level': 'show_all',
                          'activation_key': ''})

    user = authenticate(username=demo_user_uid, password=settings.DEMO_USER_ID)
    auth_login(request, user)

    return redirect('apps.dashboard.views.index')
