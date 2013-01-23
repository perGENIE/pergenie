from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template
from django.utils.translation import ugettext as _
from django.conf import settings
from apps.settings.forms import SettingsForm

import pymongo


@require_http_methods(['GET', 'POST'])
@login_required
def user_settings(request):
    user_id = request.user.username
    msg = ''
    err = ''

    if user_id == settings.DEMO_USER_ID:
        err = _('Sorry, this page is only for registered users.')
        return direct_to_template(request, 'user_settings.html', {'current_settings': {}, 'err': err, 'msg': msg, 'is_DEMO_USER': True})

    with pymongo.Connection() as connection:
        db = connection['pergenie']
        db.authenticate(settings.MONGO_USER, settings.MONGO_PASSWORD)

        user_info = db['user_info']  #

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

                user_info.update({'user_id': user_id}, {"$set": {'risk_report_show_level': show_level}}, upsert=True)

                break

        current_settings = user_info.find_one({'user_id': user_id})

        print current_settings
        if not current_settings:  # init
            user_info.update({'user_id': user_id}, {"$set": {'risk_report_show_level': 'show_all'}}, upsert=True)

    return direct_to_template(request, 'user_settings.html', {'current_settings': current_settings, 'err': err, 'msg': msg, 'is_DEMO_UESR': False})
