import sys, os
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.utils.translation import ugettext as _
from django.conf import settings
from models import *

from utils.clogging import getColorLogger
log = getColorLogger(__name__)


@login_required
def index(request):
    user_id = request.user.username
    msg, err, = '', ''
    intro_type, intros = [''], []

    while True:
        catalog_latest_new_records_data = get_latest_added_date()
        infos = get_data_infos(user_id)
        recent_catalog_records = get_recent_catalog_records()

        print user_id.startswith(settings.DEMO_USER_ID)
        if user_id.startswith(settings.DEMO_USER_ID):
            tmp_user_info = get_user_info(user_id)
            if not tmp_user_info.get('last_viewed_file'):
                intro_type = ['welcome']
            else:
                intro_type = ['invitation']

        else:
            if not infos:
                intro_type = ['first']
                break

            # for info in infos:
            #     if not info['status'] == 100:
            #         intro_type = ['wait_upload']

        break

    # Intro.js
    if intro_type == ['first']:
        intros.append(_('Welcome to perGENIE!'))
        intros.append(_('You have no genome files uploaded.'))
        intros.append(_('So, first, upload your genome file!'))
    # elif intro_type == ['wait_upload']:
    #     intros.append(_('Please wait until your genome file uploaded...'))
    # elif intro_type == ['risk_report']:
    #     intros.append(_('Browse your Risk Report!'))
    elif intro_type == ['welcome']:
        intros.append(_('Welcome to perGENIE!'))
        intros.append(_('Genome files are already uploaded for demo users.'))
        intros.append(_('So, you can check disease risk report, right now!'))
    elif intro_type == ['invitation']:
        intros.append(_('Did you have fun with perGENIE?'))
        intros.append(_('You can register account for free, at any time. Thanks for trying this demo!'))
    else:
        pass

    msgs = dict(msg=msg, err=err,
                demo_user_id=settings.DEMO_USER_ID,
                catalog_latest_new_records_data=catalog_latest_new_records_data,
                recent_catalog_records=recent_catalog_records,
                intros=intros,
                intro_type=intro_type,
                infos=infos,
                is_registerable=settings.IS_REGISTERABLE)

    return direct_to_template(request, 'dashboard/index.html', msgs)
