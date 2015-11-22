import sys, os
from smtplib import SMTPException

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.views.decorators.http import require_http_methods
from django.shortcuts import render, redirect
from django.utils.translation import ugettext as _
from django.utils.translation import get_language
from django.db import IntegrityError, transaction
from django.http import Http404
from django.template import Context
from django.template.loader import get_template
from django.core.exceptions import ObjectDoesNotExist
from django.contrib import messages
from django.conf import settings

from .forms import LoginForm, RegisterForm
from .models import UserActivation, User
from lib.utils.demo import create_demo_user, prune_demo_user
from utils import clogging
log = clogging.getColorLogger(__name__)


@require_http_methods(['GET', 'POST'])
def register(request):
    auth_logout(request)

    if request.method == 'POST':
        while True:
            form = RegisterForm(request.POST)

            if not form.is_valid():
                # FIXME
                for field in form:
                    if field.errors:
                        messages.error(request, field.errors)
                break

            try:
                with transaction.atomic():
                    user = User.objects.create_user(form.cleaned_data['email'], form.cleaned_data['email'], form.cleaned_data['password1'])
                    user.save()

                    while True:
                        try:
                            activation_key = User.objects.make_random_password(length=settings.ACCOUNT_ACTIVATION_KEY_LENGTH)
                            UserActivation(user=user, activation_key=activation_key).save()
                            break
                        except IntegrityError:
                            log.info('activation_key exists, so retry')

                    activation_url = request.build_absolute_uri(os.path.join('..', 'activation', activation_key))
                    send_activation_email(user, activation_url)

            except IntegrityError:
                messages.error(request, _('Already registered.'))
                break
            except SMTPException:
                messages.error(request, _('Invalid mail address assumed.'))
                break

            return render(request, 'registration_completed.html', dict(email=user.email))

    return render(request, 'register.html')


def activation(request, activation_key):
    try:
        activation_target = UserActivation.objects.get(activation_key=activation_key)
        user = User.objects.get(email__exact=activation_target.user.email)
    except ObjectDoesNotExist, e:
        log.error(e)
        raise Http404

    # TODO: check ACCOUNT_ACTIVATION_KYE_EXPIRE_HOURS
    # TODO: if expired, show link to re-issue activation key in view

    user.is_active = True
    user.save()
    activation_target.delete()

    send_activation_completed_email(user)

    return render(request, 'activation_completed.html')


@require_http_methods(['GET', 'POST'])
def login(request):
    if request.method == 'POST':
        while True:
            form = LoginForm(request.POST)

            if not form.is_valid():
                messages.error(request, _('invalid mail address or password'))
                break

            user = authenticate(username=form.cleaned_data['email'], password=form.cleaned_data['password'])

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

    return render(request, 'login.html')


def logout(request):
    auth_logout(request)
    return redirect('apps.authentication.views.login')

def trydemo(request):
    prune_demo_user()
    demo_user = create_demo_user()
    auth_user = authenticate(email=demo_user.email, password='')
    auth_login(request, auth_user)
    return redirect('apps.dashboard.views.index')

def send_activation_email(user, activation_url):
    email_template = get_template('activation_email.html')
    email_title = _("Welcome to perGENIE")
    email_body = email_template.render(Context({'activation_url': activation_url, 'support_email': settings.SUPPORT_EMAIL}))
    user.email_user(subject=email_title, message=email_body, from_email=settings.NOREPLY_EMAIL)

def send_activation_completed_email(user):
    email_template = get_template('activation_completed_email.html')
    email_title = _('Your account has been activated')
    email_body = email_template.render(Context({'support_email': settings.SUPPORT_EMAIL}))
    user.email_user(subject=email_title, message=email_body, from_email=settings.NOREPLY_EMAIL)
