import sys, os
import socket
# from uuid import uuid4

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.utils.translation import ugettext as _
from django.utils.translation import get_language
from django.db import IntegrityError, transaction
from django.http import Http404
from django.template import Context
from django.template.loader import get_template
from django.contrib import messages
from django.conf import settings

from apps.authentication.forms import LoginForm, RegisterForm
from apps.authentication.models import UserActivation
from utils import clogging
log = clogging.getColorLogger(__name__)


def about_service(request):
    return render(request, 'authentication/about_service.html')


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

            log.debug(user_id)

            try:
                with transaction.atomic():
                    user = User.objects.create_user(user_id, user_id, password1)
                    if settings.ACCOUNT_ACTIVATION_REQUIRED:
                        user.is_active = False
                        _send_activation_email(user, request)
                        user.save()
                        return render(request, 'authentication/registration_completed.html', dict(user_id=user_id))
                    else:
                        user.is_active = True
                        user.save()
                        auth_login(request, authenticate(username=user_id, password=password1))
                        return redirect('apps.dashboard.views.index')
            except Exception, e:
                log.error(e)
                messages.error(request, _('Invalid request.'))
                break

    return render(request, 'authentication/register.html')


def activation(request, activation_key):
    try:
        challenging_user = UserActivation.objects.get(activation_key=activation_key)
        if not challenging_user:
            raise Exception('Invalid activation_key')

        user = User.objects.get(username__exact=challenging_user.user.username)
        if user:
            # TODO: check ACCOUNT_ACTIVATION_KYE_EXPIRE_HOURS
            # TODO: if expired, show link to re-issue activation key in view

            user.is_active = True
            user.save()
            challenging_user.delete()
            _send_activation_completed_email(user)
    except Exception, e:
        log.error(e)
        raise Http404

    return render(request, 'authentication/activation_completed.html')


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
#     return redirect('apps.dashboard.views.index')


# def logoutdemo(request):
#     auth_logout(request)
#     return redirect('apps.authentication.views.index')


def _send_activation_email(user, request):
    activation_key = User.objects.make_random_password(length=settings.ACCOUNT_ACTIVATION_KEY_LENGTH)
    activation_url = request.build_absolute_uri(os.path.join('..', 'activation', activation_key))

    try:
        with transaction.atomic():
            ua = UserActivation(user=user, activation_key=activation_key)
            ua.save()

            email_template = get_template('authentication/activation_email.html')
            email_title = _("Welcome to perGENIE")
            email_body = email_template.render(Context({'activation_url': activation_url, 'support_email': settings.SUPPORT_EMAIL}))
            user.email_user(subject=email_title, message=email_body)
    except Exception as e:
        log.error(e)
        log.error('send activaton email failed')

        prev_user = User.objects.filter(username=user.username)
        if prev_user:
            prev_user.delete()

        raise Exception(_('Invalid mail address assumed.'))

def _send_activation_completed_email(user):
    email_template = get_template('authentication/activation_completed_email.html')
    email_title = _('Your account has been activated')
    email_body = email_template.render(Context({'support_email': settings.SUPPORT_EMAIL}))
    user.email_user(subject=email_title, message=email_body)
