import sys, os
from uuid import uuid4

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.utils.translation import ugettext as _
from django.utils.translation import get_language
from django.db import IntegrityError
from django.http import Http404
from django.contrib import messages
from django.conf import settings

from apps.authentication.forms import LoginForm, RegisterForm
from lib.api.user import User as pergenie_User
from utils import clogging
log = clogging.getColorLogger(__name__)


@require_http_methods(['GET', 'POST'])
def register(request):
    auth_logout(request)

    if request.method == 'POST':
        while True:
            form = RegisterForm(request.POST)

            if not form.is_valid():
                messages.error(request, _('Invalid request.'))  # contains case for null input
                break

            user_id = form.cleaned_data['user_id']
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']
            terms_ok_0 = form.cleaned_data['terms_ok_0']
            terms_ok_1 = form.cleaned_data['terms_ok_1']

            # Not read and accept terms of service
            if not terms_ok_0 or not terms_ok_1:
                messages.error(request, _('Not read and accept about service of perGENIE.'))
                break

            if password1 != password2:
                messages.error(request, _('Passwords do not match.'))
                break

            u = pergenie_User()
            try:
                u.create(user_id, password1)
            except Exception, e:
                log.error(e)
                messages.error(request, _('Invalid request.'))
                break

            # Registration *without* mail verification
            if not settings.ACCOUNT_ACTIVATION:
                user = User.objects.filter(username=user_id)
                auth_login(request, user)
                return redirect('apps.dashboard.views.index')

            log.debug(user_id)

            try:
                u.send_activation_email(user_id)
            except Exception, e:
                log.error(e)
                messages.error(request, _('Invalid request.'))
                break

            return render(request, 'authentication/registration_completed.html', dict(user_id=user_id))

    return render(request, 'authentication/register.html', dict(browser_language=get_language()))


# def activation(request, activation_key):
#     u = pergenie_User()
#     try:
#         u.activate(activation_key)
#     except Exception, e:
#         log.error(e)
#         raise Http404

#     return direct_to_template(request, 'authentication/activation_completed.html')


@require_http_methods(['GET', 'POST'])
def login(request):
    if request.method == 'POST':
        while True:
            form = LoginForm(request.POST)

            if not form.is_valid():
                messages.error(request, _('Invalid request.'))
                break

            user_id = form.cleaned_data['user_id']
            password = form.cleaned_data['password']

            if settings.ALLOWED_EMAIL_DOMAINS:
                if not user_id.split('@')[-1] in settings.ALLOWED_EMAIL_DOMAINS:
                    messages.error(request, _('invalid mail address or password'))

                    log.warn('Attempt to login by not allowed email domain: %s' % user_id)
                    # TODO: error mail
                    # send_mail(subject='warn',
                    #           message='Attempt to login by not allowed email domain: %s' % user_id,
                    #           from_email=settings.EMAIL_HOST_USER,
                    #           recipient_list=[settings.EMAIL_HOST_USER],
                    #           fail_silently=False)
                    break

            user = authenticate(username=user_id, password=password)

            if user is None:
                messages.error(request, _('invalid mail address or password'))
                break

            if not user.is_active:
                messages.error(request, _('invalid mail address or password'))
                break

            auth_login(request, user)

            # TODO: Remember Me
            # if not request.POST.get('remember_me', None):
            #     request.session.set_expiry(0)
            #     log.debug("Not Remember Me")

            return redirect('apps.dashboard.views.index')

    return render(request, 'authentication/login.html')


def logout(request):
    auth_logout(request)
    return redirect('apps.authentication.views.login')


# def trydemo(request):
#     """Login as DEMO USER (demo@pergenie.org)
#     """

#     while True:
#         try:
#             demo_user_uid = settings.DEMO_USER_ID + '+' + str(uuid4())
#             user = User.objects.create_user(demo_user_uid, '', settings.DEMO_USER_ID)
#             user.save()
#             break
#         except IntegrityError, e:
#             pass
#         except:
#             return direct_to_template(request, 'authentication/index.html')

#     # create user_info
#     with MongoClient(host=settings.MONGO_URI) as c:
#         user_info = c['pergenie']['user_info']

#         user_info.insert({'user_id': demo_user_uid,
#                           'risk_report_show_level': 'show_all',
#                           'activation_key': ''})

#     user = authenticate(username=demo_user_uid, password=settings.DEMO_USER_ID)
#     auth_login(request, user)

#     return redirect('apps.dashboard.views.index')


# def logoutdemo(request):
#     auth_logout(request)
#     return redirect('apps.authentication.views.index')
