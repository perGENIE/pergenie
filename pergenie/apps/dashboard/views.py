# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.utils.translation import ugettext as _
from django.conf import settings
from models import *

import sys, os
from pprint import pformat
import pymongo

from utils.date import today_date
from utils.clogging import getColorLogger
log = getColorLogger(__name__)


@login_required
def index(request):
    user_id = request.user.username
    msg, err, warns = '', '', []
    n_new_records = 0
    do_intro, do_intro_risk_report = False, False
    intros = list()

    while True:
        catalog_latest_new_records_data = get_latest_added_date()
        infos = get_data_infos(user_id)

        # user's latest riskreport date

        # for info in infos:
        #     risk_report_latest_date[user_data['name']] = user_data.get('riskreport', None)

        #     if risk_report_latest_date[user_data['name']]:
        #         # if riskreport is outdated, show diff of records (& link to riskreport)
        #         if today_date > user_data['riskreport']:
        #             warns.append('Risk-Report for "{}" outdated!'.format(user_data['name']))
        #             # warn += '\n last risk report: {}'.format(user_data['riskreport'])

        #         # for added_date in sorted(catalog_summary.get('added').items()):
        #         #     # print added_date[0],  catalog_latest_importing_document['date']
        #         #     if added_date[0] > catalog_latest_importing_document['date']:
        #         #         msg += '\n {1} new records {0}'.format(added_date[0], added_date[1])

        # determine file
        # infos = list(data_info.find( {'user_id': user_id} ))

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

    msgs = {'msg': msg, 'err': err, 'warns': warns, 'user_id': user_id,
            'catalog_latest_new_records_data': catalog_latest_new_records_data,
            'risk_report_latest_date': risk_report_latest_date,
            'n_new_records': n_new_records,
            'do_intro': do_intro, 'do_intro_risk_report': do_intro_risk_report,
            'intros': intros, 'infos': infos}

    log.info('msgs: {}'.format(pformat(msgs)))
    return direct_to_template(request, 'dashboard.html', msgs)
