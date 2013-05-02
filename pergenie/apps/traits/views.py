# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template
from django.utils.translation import get_language
from django.utils.translation import ugettext as _
from django.conf import settings

from apps.riskreport.forms import RiskReportForm

import os
import pymongo
# import numpy as np

# #
# import mongo.search_variants as search_variants
# import mongo.risk_report as risk_report

# #
# from lib.mongo.get_latest_catalog import get_latest_catalog
from lib.mongo.get_traits_infos import get_traits_infos
# from utils.io import pickle_dump_obj, pickle_load_obj
# from utils.date import today_date, today_str
from utils import clogging
log = clogging.getColorLogger(__name__)

TRAITS, TRAITS2JA, TRAITS2CATEGORY = get_traits_infos(as_dict=True)
JA2TRAITS = dict([(v, k) for (k, v) in TRAITS2JA.items()])


# @require_http_methods(['GET', 'POST'])
@login_required
def index(request):
    user_id = request.user.username
    msg, err = '', ''
    browser_language = get_language()

    # with pymongo.Connection(port=settings.MONGO_PORT) as connection:
    #     data_info = connection['pergenie']['data_info']

    #     while True:
    #         # determine file
    #         infos = list(data_info.find({'user_id': user_id}))
    #         tmp_info = None
    #         tmp_infos = []

    #         if not infos:
    #             err = _('no data uploaded')
    #             break

    #         if request.method == 'POST':
    #             """User chose file_name via select box & requested as POST
    #             """

    #             log.debug('method == POST')

    #             form = RiskReportForm(request.POST)
    #             if not form.is_valid():
    #                 err = _('Invalid request.')
    #                 break

    #             for i, file_name in enumerate([request.POST['file_name'], request.POST['file_name2']]):
    #                 log.debug('file_name: {0} from form: {1}'.format(i+1, file_name))

    #                 for info in infos:
    #                     if info['name'] == file_name:
    #                         if not info['status'] == 100:
    #                             # err = str(file_name) + _(' is in importing, please wait for seconds...')
    #                             err = _('%(file_name)s is in importing, please wait for seconds...') % {'file_name': file_name}

    #                         tmp_info = info
    #                         tmp_infos.append(tmp_info)
    #                         break

    #                 if not tmp_info:
    #                     err = _('no such file %(file_name)s') % {'file_name': file_name}
    #                     break

    #         else:
    #             log.debug('method != POST')

    #             # choose first file_name by default
    #             info = infos[0]
    #             file_name = info['name']
    #             if not info['status'] == 100:
    #                 err = _('%(file_name)s is in importing, please wait for seconds...') % {'file_name': file_name}
    #             tmp_infos.append(info)

    #         if not err:
    #             risk_reports, risk_traits, risk_values = get_risk_values_for_indexpage(tmp_infos, category=['Disease'])

    #             # translate to Japanese
    #             if browser_language == 'ja':
    #                 risk_traits = [TRAITS2JA.get(trait) for trait in risk_traits]
    #         break

    return direct_to_template(request, 'traits.html', {})
                                  # dict(user_id=user_id, msg=msg, err=err, infos=infos, tmp_infos=tmp_infos,
                                  #      risk_reports=risk_reports, risk_traits=risk_traits, risk_values=risk_values))
