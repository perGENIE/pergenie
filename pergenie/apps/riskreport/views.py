# -*- coding: utf-8 -*-
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template
from django.shortcuts import redirect
from django.utils.translation import get_language
from django.utils.translation import ugettext as _
from django.conf import settings
from models import *
from apps.riskreport.forms import RiskReportForm

import sys, os

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
    do_intro = False

    h_risk_traits, h_risk_values, h_risk_ranks, h_risk_studies = None, None, None, None

    while True:
        # determine file
        infos = get_user_data_infos(user_id)
        tmp_info = None

        if not infos:
            err = _('no data uploaded')
            break

        # If this is the first time for riskreport,
        if [bool(info.get('riskreport')) for info in infos].count(True) == 0:
            do_intro = True

        # By default, browse `last_viewed_file`
        if not request.method == 'POST':
            tmp_user_info = get_user_info(user_id)
            if tmp_user_info.get('last_viewed_file'):
                file_name = tmp_user_info['last_viewed_file']
                info = get_user_file_info(user_id, file_name)

            # If this is the first time, choose first file_name in infos.
            else:
                info = infos[0]
                file_name = info['name']

            if not info['status'] == 100:
                err = _('%(file_name)s is in importing, please wait for seconds...') % {'file_name': file_name}
                break
            else:
                tmp_info = info

        # If file_name is selected by user with Form,
        elif request.method == 'POST':
            form = RiskReportForm(request.POST)
            if not form.is_valid():
                err = _('Invalid request.')
                break

            file_name = request.POST['file_name']
            for info in infos:
                if info['name'] == file_name:
                    if not info['status'] == 100:
                        err = _('%(file_name)s is in importing, please wait for seconds...') % {'file_name': file_name}
                    else:
                        tmp_info = info
                    break

            if not tmp_info:
                err = _('no such file %(file_name)s') % {'file_name': file_name}
                break

        # Selected file_name exists & has been imported, so calculate risk.
        if not err:
            # get top-10 highest & top-10 lowest
            h_risk_traits, h_risk_values, h_risk_ranks, h_risk_studies = get_risk_values_for_indexpage(tmp_info, category=['Disease'], is_higher=True, top=10, is_log=False)

            # set `last_viewed_file`
            set_user_last_viewed_file(user_id, file_name)

            # translate to Japanese
            if browser_language == 'ja':
                h_risk_traits = [TRAITS2JA.get(trait) for trait in h_risk_traits]

        break

    return direct_to_template(request, 'risk_report/index.html',
                              dict(msg=msg, err=err, infos=infos, tmp_info=tmp_info, do_intro=do_intro,
                                   h_risk_traits=h_risk_traits, h_risk_values=h_risk_values,
                                   h_risk_ranks=h_risk_ranks, h_risk_studies=h_risk_studies
                                   ))


@login_required
def study(request, trait, study):
    user_id = request.user.username
    msg, err = '', ''

    while True:
        trait = JA2TRAITS.get(trait, trait)

        if not trait in TRAITS:
            err = _('trait not found')
            break

        file_name = get_user_info(user_id).get('last_viewed_file')

        # If you have no riskreports, but this time you try to browse details of reprort,
        if not file_name:
            return redirect('apps.riskreport.views.index')

        info = get_user_file_info(user_id, file_name)

        if not info:
            err = _('no such file %(file_name)s') % {'file_name': file_name}
            break

        # Trait & file_name exists, so get the risk information about this trait.
        risk_infos = get_risk_infos_for_subpage(info, trait=trait, study=study)
        risk_infos.update(dict(msg=msg, err=err, file_name=file_name, info=info,
                               wiki_url_en=TRAITS2WIKI_URL_EN.get(trait),
                               is_ja=bool(get_language() == 'ja')))
        break

    return direct_to_template(request, 'risk_report/study.html', risk_infos)


@login_required
def trait(request, trait):
    """Show risk value by studies, for each trait.
    """

    # user_id = request.user.username
    # trait = JA2TRAITS.get(trait, trait)
    # risk_infos = get_risk_infos_for_subpage(user_id, file_name, trait)

    # risk_infos.update(dict(msg=msg, err=err, file_name=file_name,
    #                        wiki_url_en=TRAITS2WIKI_URL_EN.get(trait),
    #                        is_ja=bool(get_language() == 'ja')))

    # return direct_to_template(request, 'risk_report/trait.html', risk_infos)
    return redirect('apps.riskreport.views.index')


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
    # risk_reports, risk_traits, risk_values = None, None, None
    risk_traits, risk_values, risk_ranks, risk_studies = [], [], [], []
    browser_language = get_language()

    while True:
        # determine file
        infos = get_user_data_infos(user_id)
        tmp_info = None
        tmp_infos = []
        data_map = {}

        if not infos:
            err = _('no data uploaded')
            break

        if not request.method == 'POST':
            file_name = get_user_info(user_id).get('last_viewed_file')

            # If you have no riskreports, but this time you try to browse details of reprort,
            if not file_name:
                return redirect('apps.riskreport.views.index')

            tmp_infos.append(get_user_file_info(user_id, file_name))

        # If file_name is selected by user with Form,
        elif request.method == 'POST':
            # form = RiskReportForm(request.POST)
            # if not form.is_valid():
            #     err = _('Invalid request.')
            #     break

            # for i, file_name in enumerate([request.POST['file_name'], request.POST['file_name2']]):
            #     log.debug('file_name: {0} from form: {1}'.format(i+1, file_name))

            #     for info in infos:
            #         if info['name'] == file_name:
            #             if not info['status'] == 100:
            #                 err = _('%(file_name)s is in importing, please wait for seconds...') % {'file_name': file_name}

            #             tmp_info = info
            #             tmp_infos.append(tmp_info)
            #             break

            #     if not tmp_info:
            #         err = _('no such file %(file_name)s') % {'file_name': file_name}
            #         break
            pass

        if not err:
            for i,tmp_info in enumerate(tmp_infos):
                tmp_risk_traits, tmp_risk_values, tmp_risk_ranks, tmp_risk_studies = get_risk_values_for_indexpage(tmp_infos[i], category=['Disease'])

                if i == 0:
                    risk_traits = tmp_risk_traits

                risk_values.append(tmp_risk_values[0])
                risk_ranks.append(tmp_risk_ranks)
                risk_studies.append(tmp_risk_studies)

            # translate to Japanese
            if browser_language == 'ja':
                risk_traits = [TRAITS2JA.get(trait) for trait in risk_traits]

        break

    return direct_to_template(request, 'risk_report/show_all.html',
                              dict(msg=msg, err=err, infos=infos, tmp_infos=tmp_infos,
                                   risk_traits=risk_traits, risk_values=risk_values, risk_ranks=risk_ranks, risk_studies=risk_studies))
