# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.utils.translation import ugettext as _
from django.conf import settings
from models import *

import sys, os
from pprint import pformat
import pymongo

from utils.clogging import getColorLogger
log = getColorLogger(__name__)


@login_required
def index(request):
    user_id = request.user.username
    msg, err, = '', ''
    msgs = []
    n_out_dated_riskreports = 0
    intro_type, intros = [''], []

    while True:
        catalog_latest_new_records_data = get_latest_added_date()
        infos = get_data_infos(user_id)
        recent_catalog_records = get_recent_catalog_records()

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

            intro_type = ['wait_upload']

            # check if latest riskreports are outdated
            for info in infos:
                risk_report_latest_date = info.get('riskreport')

                if risk_report_latest_date:
                    # If there is at least one riskreported file,
                    intro_type = []

                    if risk_report_latest_date.date() < catalog_latest_new_records_data:
                        msgs.append('Risk report outdated, so re-calculate riskreport: {0}'.format(info['raw_name']))
                        n_out_dated_riskreports += 1

                elif info['status'] == 100:
                    # If there is at least one 100% uploaded file,
                    intro_type = ['risk_report']

                else:
                    pass
        break

    # Intro.js
    if intro_type == ['first']:
        intros.append('Welcome to perGENIE!')
        intros.append('You have no genome files uploaded.')
        intros.append('So, first, upload your genome file!')
    elif intro_type == ['wait_upload']:
        intros.append('Please wait until your genome file uploaded...')
    elif intro_type == ['risk_report']:
        intros.append('Browse your Risk Report!')
    elif intro_type == ['welcome']:
        intros.append('Welcome to perGENIE!')
        intros.append('Genome files are already uploaded for demo users.')
        intros.append('So, you can check disease risk report, right now!')
    elif intro_type == ['invitation']:
        intros.append('Did you have fun with perGENIE?')
        intros.append('You can register account for free, at any time. Thanks for trying this demo!')
    else:
        pass

    msgs = dict(msg=msg, err=err, msgs=msgs, user_id=user_id, demo_user_id=settings.DEMO_USER_ID,
                catalog_latest_new_records_data=catalog_latest_new_records_data,
                n_out_dated_riskreports=n_out_dated_riskreports,
                recent_catalog_records=recent_catalog_records,
                intros=intros, intro_type=intro_type, infos=infos)

    return direct_to_template(request, 'dashboard/index.html', msgs)
