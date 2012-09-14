from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.views.decorators.http import require_http_methods
from frontend.forms import LoginForm, RegisterForm

import pymongo


def index(request):
    return redirect('frontend.views.login')


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
                return redirect('dashboard.views.index')

            else:
                params['error'] = 'invalid mail address or password'

        else:
            params['error'] = 'Invalid request'

    return _render_to_response('login.html', params, request)


def logout(request):
    auth_logout(request)
    return redirect('frontend.views.index')


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

            if password1 == password2:
                try:
                    user = User.objects.create_user(user_id, user_id, password1)
                    user.save()

                except:
                    params['has_error'] = True
                    params['message'] = 'Already registered'

                else:
                    with pymongo.Connection() as connection:
                        db = connection['pergenie']
                        users = db['users']
                        users.insert({'user_id': user_id})

                    params['is_succeeded'] = True
                    params['message'] = 'You have successfully registered!'

            else:
                params['has_error'] = True
                params['message'] = 'Passwords doesn\'t match'


        else:
            params['has_error'] = True
            params['message'] = 'Invalid request'


    return _render_to_response('register.html', params, request)


def settings(request):
    pass


def about(request):
    return render_to_response('about.html')


def _render_to_response(template, params, request):
    return render_to_response(template,
                              params,
                              context_instance=RequestContext(request))
