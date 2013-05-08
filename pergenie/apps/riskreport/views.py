# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template
from django.utils.translation import get_language
from django.utils.translation import ugettext as _
from django.conf import settings
from models import *
from apps.riskreport.forms import RiskReportForm

# import sys, os
# import re

#
from utils.io import pickle_dump_obj, pickle_load_obj
from utils.date import today_date, today_str
from utils import clogging
log = clogging.getColorLogger(__name__)


@require_http_methods(['GET', 'POST'])
@login_required
def index(request):
    """
    Summary view for risk report.
    * Show top-10 highest & top-10 lowest risk values.
    * Link to `show all`
    """
    user_id = request.user.username
    msg, err = '', ''
    browser_language = get_language()

    while True:
        # determine file
        infos = get_user_infos(user_id)
        tmp_info = None
        tmp_infos = []

        if not infos:
            err = _('no data uploaded')
            break

        if request.method == 'POST':
            form = RiskReportForm(request.POST)
            if not form.is_valid():
                err = _('Invalid request.')
                break

            for i, file_name in enumerate([request.POST['file_name']]):
                for info in infos:
                    if info['name'] == file_name:
                        if not info['status'] == 100:
                            err = _('%(file_name)s is in importing, please wait for seconds...') % {'file_name': file_name}

                        tmp_info = info
                        tmp_infos.append(tmp_info)
                        break

                if not tmp_info:
                    err = _('no such file %(file_name)s') % {'file_name': file_name}
                    break

        else:
            # choose first file_name by default
            info = infos[0]
            file_name = info['name']
            if not info['status'] == 100:
                err = _('%(file_name)s is in importing, please wait for seconds...') % {'file_name': file_name}
            tmp_infos.append(info)

        if not err:
            # get top-10 highest & top-10 lowest
            h_risk_traits, h_risk_values, h_risk_ranks, h_risk_studies = get_risk_values_for_indexpage(tmp_infos[0], category=['Disease'], is_higher=True, top=10, is_log=False)

            # translate to Japanese
            if browser_language == 'ja':
                h_risk_traits = [TRAITS2JA.get(trait) for trait in h_risk_traits]

        break

    return direct_to_template(request, 'risk_report/index.html',
                              dict(msg=msg, err=err, infos=infos, tmp_infos=tmp_infos,
                                   h_risk_traits=h_risk_traits, h_risk_values=h_risk_values,
                                   h_risk_ranks=h_risk_ranks, h_risk_studies=h_risk_studies
                                   ))


@login_required
def study(request, file_name, trait, study):
    user_id = request.user.username
    msg, err = '', ''

    while True:
        if not JA2TRAITS.get(trait, trait) in TRAITS:
            err = _('trait not found')
            break

        info = get_user_file_info(user_id, file_name)

        if not info:
            err = _('no such file %(file_name)s') % {'file_name': file_name}
            break

        trait = JA2TRAITS.get(trait, trait)
        risk_infos = get_risk_infos_for_subpage(info, trait=trait, study=study)
        risk_infos.update(dict(msg=msg, err=err, file_name=file_name,
                               wiki_url_en=TRAITS2WIKI_URL_EN.get(trait),
                               is_ja=bool(get_language() == 'ja')))
        break

    return direct_to_template(request, 'risk_report/study.html', risk_infos)


@login_required
def trait(request, file_name, trait):
    """Show risk value by studies, for each trait.
    """

    user_id = request.user.username
    trait = JA2TRAITS.get(trait, trait)
    risk_infos = get_risk_infos_for_subpage(user_id, file_name, trait)

    risk_infos.update(dict(msg=msg, err=err, file_name=file_name,
                           wiki_url_en=TRAITS2WIKI_URL_EN.get(trait),
                           is_ja=bool(get_language() == 'ja')))

    return direct_to_template(request, 'risk_report/trait.html', risk_infos)




@require_http_methods(['GET', 'POST'])
@login_required
def show_all(request):
    """
    Show all risk values in a chart.
    * It can compare two individual genomes.

    TODO:
    * Do not use log-scale. Replace to real-scale.
    * Enable to click & link trait-name in charts. (currently bar in charts only)
    * Show population in charts, e.g., `Japanese national flag`, etc.
    """

    user_id = request.user.username
    msg, err = '', ''
    risk_reports, risk_traits, risk_values = None, None, None
    browser_language = get_language()

    while True:
        # determine file
        infos = get_user_infos(user_id)
        tmp_info = None
        tmp_infos = []

        if not infos:
            err = _('no data uploaded')
            break

        if request.method == 'POST':
            """User chose file_name via select box & requested as POST
            """

            log.debug('method == POST')

            form = RiskReportForm(request.POST)
            if not form.is_valid():
                err = _('Invalid request.')
                break

            for i, file_name in enumerate([request.POST['file_name'], request.POST['file_name2']]):
                log.debug('file_name: {0} from form: {1}'.format(i+1, file_name))

                for info in infos:
                    if info['name'] == file_name:
                        if not info['status'] == 100:
                            # err = str(file_name) + _(' is in importing, please wait for seconds...')
                            err = _('%(file_name)s is in importing, please wait for seconds...') % {'file_name': file_name}

                        tmp_info = info
                        tmp_infos.append(tmp_info)
                        break

                if not tmp_info:
                    err = _('no such file %(file_name)s') % {'file_name': file_name}
                    break

        else:
            log.debug('method != POST')

            # choose first file_name by default
            info = infos[0]
            file_name = info['name']
            if not info['status'] == 100:
                err = _('%(file_name)s is in importing, please wait for seconds...') % {'file_name': file_name}
            tmp_infos.append(info)

        if not err:
            risk_reports, risk_traits, risk_values, risk_ranks, risk_studies = get_risk_values_for_indexpage(tmp_infos, category=['Disease'])

            # translate to Japanese
            if browser_language == 'ja':
                risk_traits = [TRAITS2JA.get(trait) for trait in risk_traits]
        break

    return direct_to_template(request, 'risk_report/show_all.html',
                              dict(msg=msg, err=err, infos=infos, tmp_infos=tmp_infos,
                                   risk_reports=risk_reports, risk_traits=risk_traits, risk_values=risk_values, risk_studies=risk_studies))
