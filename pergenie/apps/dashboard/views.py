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
    msg, err, warns = '', '', []
    n_out_dated_riskreports = 0
    do_intro, do_intro_risk_report = False, False
    intros = []

    while True:
        catalog_latest_new_records_data = get_latest_added_date()
        infos = get_data_infos(user_id)

        # check if latest riskreports are outdated
        for info in infos:
            risk_report_latest_date = info.get('riskreport')

            if risk_report_latest_date:
                if risk_report_latest_date.date() < catalog_latest_new_records_data:
                    warns.append('risk report outdated: {}'.format(info['name']))
                    n_out_dated_riskreports += 1

        # Intro.js
        if not infos:
            do_intro = True
            # Translators: This message appears on the home page only
            intros.append(_('First, upload your genome file!'))
            intros.append(_('Next, ....'))
        else:
            # TODO: check if {status == 100}
            do_intro_risk_report = True
            intros.append('Browse your Risk Report!')

        break

    log.debug(infos)

    msgs = dict(msg=msg, err=err, warns=warns, user_id=user_id,
                catalog_latest_new_records_data=catalog_latest_new_records_data,
                n_out_dated_riskreports=n_out_dated_riskreports,
                do_intro=do_intro, do_intro_risk_report=do_intro_risk_report,
                intros=intros, infos=infos)

    return direct_to_template(request, 'dashboard.html', msgs)
