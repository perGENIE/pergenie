# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template
from django.conf import settings

from apps.settings.forms import SettingsForm

from pymongo import MongoClient


@require_http_methods(['GET', 'POST'])
@login_required
def user_settings(request):
    user_id = request.user.username
    msg, err = '', ''

    with MongoClient(port=settings.MONGO_PORT) as c:
        user_info = c['pergenie']['user_info']

        if request.method == 'POST':
            while True:
                form = SettingsForm(request.POST, request.FILES)

                if not form.is_valid():
                    err = 'Invalid request'
                    break

                show_level = form.cleaned_data['show_level']

                if not show_level:
                    err = 'Select show level.'
                    break

                user_info.update({'user_id': user_id},
                                 {"$set": {'risk_report_show_level': show_level}},
                                 upsert=True)
                msg = 'Changes were successfully saved.'
                break

        current_settings = user_info.find_one({'user_id': user_id})

        if not current_settings:  # init
            user_info.update({'user_id': user_id},
                             {"$set": {'risk_report_show_level': 'show_all'}},
                             upsert=True)

    return direct_to_template(request, 'user_settings.html',
                              dict(msg=msg, err=err,
                                   current_settings=current_settings))
