# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template
from django.conf import settings

from apps.settings.forms import SettingsForm

from pymongo import MongoClient
from utils.clogging import getColorLogger
log = getColorLogger(__name__)


@require_http_methods(['GET', 'POST'])
@login_required
def user_settings(request):
    user_id = request.user.username
    msg, err = '', ''

    with MongoClient(host=settings.MONGO_URI) as c:
        user_info = c['pergenie']['user_info']

        if request.method == 'POST':
            while True:
                form = SettingsForm(request.POST)

                if not form.is_valid():
                    err = 'Invalid request'
                    break

                show_level = form.cleaned_data['show_level']
                exome_ristricted = form.cleaned_data['exome_ristricted']
                use_log = form.cleaned_data['use_log']

                if not show_level:
                    err = 'Select show level.'
                    break

                user_info.update({'user_id': user_id},
                                 {"$set": {'risk_report_show_level': show_level,
                                           'exome_ristricted': exome_ristricted,
                                           'use_log': use_log}},
                                 upsert=True)
                msg = 'Changes were successfully saved.'
                break

        current_settings = user_info.find_one({'user_id': user_id})

        if not current_settings:  # init
            user_info.update({'user_id': user_id},
                             {"$set": {'risk_report_show_level': 'show_all',
                                       'exome_ristricted': False,
                                       'use_log': False}},
                             upsert=True)

    return direct_to_template(request, 'user_settings.html',
                              dict(msg=msg, err=err,
                                   current_settings=current_settings))
