import sys
import os
import datetime

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.shortcuts import redirect, render
# from django.http import HttpResponse, Http404
# from django.utils.translation import get_language
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.conf import settings
from django.db.models import Q

from apps.authentication.models import User
from apps.genome.models import Genome
from apps.gwascatalog.models import GwasCatalogSnp
from .forms import RiskReportForm
from .models import RiskReport, PhenotypeRiskReport, SnpRiskReport
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


@require_http_methods(['GET', 'POST'])
@login_required
def index(request):
    """Summary view for risk reports.

    - Show top 10 highest risk values for one selected riskreport.
    - Show link to `show all phenotypes`
    - Show only latest for each riskreport.
    """

    while True:
        user = User.objects.filter(id=request.user.id)
        owner_genomes = Genome.objects.filter(owner=user)
        reader_genomes = Genome.objects.filter(readers__in=user)

        # Get only latest for each riskreport.
        risk_reports = []
        for readable_report in RiskReport.objects.distinct('genome').filter(Q(genome__owner=user) | Q(genome__readers=user)):
            risk_reports.append(RiskReport.objects.filter(genome=readable_report.genome).latest('created_at'))

        if len(risk_reports) < 1:
            messages.error(request, _('No risk reports available.'))
            break

        if request.method == 'POST':
            form = RiskReportForm(request.POST)
            if not form.is_valid():
                messages.error(request, _('Invalid request.'))
                break

            genome_id = request.POST.get('genome_id')

        else:
            # TODO: Get `last_viewed_report` cookie
            risk_report = risk_reports[0]

        # Get top-10 highest
        top_10 = PhenotypeRiskReport.objects.filter(risk_report=risk_report).exclude(estimated_risk__isnull=True).order_by('-estimated_risk')[0:10]
        top_10_names = top_10.values_list('phenotype__name', flat=True)
        top_10_risks = top_10.values_list('estimated_risk', flat=True)

        break

    # TODO: Set `last_viewed_report` cookie

    return render(request, 'riskreport.html',
                  dict(risk_reports=risk_reports,
                       risk_report=risk_report,
                       top_10_names=top_10_names,
                       top_10_risks=top_10_risks
                  ))

@require_http_methods(['GET'])
@login_required
def study(request, trait, study):
    pass
#     user_id = request.user.username
#     msg, err = '', ''
#     risk_infos = None

#     while True:
#         trait = JA2TRAITS.get(trait, trait)
#         trait_eng = trait

#         if not trait in TRAITS:
#             err = _('trait not found')
#             raise Http404

#         # # no need ?
#         # if not request.method == 'GET':
#         #     return redirect('apps.riskreport.views.index')

#         # Determine `file_name`.
#         # If file_name is selected,
#         file_name = request.GET.get('file_name')

#         if not file_name:
#             # By default, browse `last_viewed_file`
#             file_name = user.get_user_info(user_id).get('last_viewed_file')

#             # If you have no riskreports, but this time you try to browse details of reprort,
#             if not file_name:
#                 return redirect('apps.riskreport.views.index')

#         info = genomes.get_data_info(user_id, file_name)

#         if not info:
#             err = _('no such file %(file_name)s') % {'file_name': file_name}
#             raise Http404

#         # Trait & file_name exists, so get the risk information about this trait.
#         risk_infos = get_risk_infos_for_subpage(info, trait=trait, study=study)
#         risk_infos.update(dict(msg=msg, file_name=file_name, info=info, trait_eng=trait_eng,
#                                wiki_url_en=TRAITS2WIKI_URL_EN.get(trait),
#                                is_ja=bool(get_language() == 'ja')))
#         break

#     return direct_to_template(request, 'risk_report/study.html', risk_infos)

@login_required
def export(request):
    """Download riskreport
    """
    pass
#     user_id = request.user.username
#     file_name = request.GET.get('file_name')

#     # if file_name:
#     #     file_info = genomes.get_data_info(user_id, file_name)
#     #     file_infos = [file_info] if file_info else []
#     # else:
#     #     file_infos = genomes.get_data_infos(user_id)
#     # if not file_infos:
#     #     raise Http404

#     # fout_path = riskreport.write_riskreport(user_id, file_infos)
#     # if not fout_path:
#     raise Http404

#     # mimetype = {'csv': 'application/comma-separated-values',
#     #             'tsv': 'application/tab-separated-values',
#     #             'zip': 'application/zip'}

#     # fout = open(fout_path, 'rb').read()
#     # response = HttpResponse(fout, mimetype='application/zip')
#     # response['Content-Disposition'] = 'filename=' + os.path.basename(fout_path)
#     # return response

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
    pass
#     user_id = request.user.username
#     msg, err = '', ''
#     # risk_reports, risk_traits, risk_values = None, None, None
#     risk_traits, risk_values, risk_ranks, risk_studies = [], [], [], []
#     do_intro = False
#     browser_language = get_language()

#     while True:
#         # determine file
#         infos = genomes.get_data_infos(user_id)
#         tmp_info = None
#         tmp_infos = []

#         if not infos:
#             err = _('no data uploaded')
#             break

#         if not request.method == 'POST':
#             tmp_user_info = user.get_user_info(user_id)
#             file_name = tmp_user_info.get('last_viewed_file')

#             # If you have no riskreports, but this time you try to browse details of reprort,
#             if not file_name:
#                 return redirect('apps.riskreport.views.index')

#             tmp_infos.append(genomes.get_data_info(user_id, file_name))

#             # Intro.js
#             if not tmp_user_info.get('viewed_riskreport_showall'):
#                 log.debug(tmp_user_info.get('viewed_riskreport_showall'))
#                 user.set_user_viewed_riskreport_showall_done(user_id)
#                 do_intro = True

#         # If file_name is selected by user with Form,
#         elif request.method == 'POST':
#             form = RiskReportForm(request.POST)
#             if not form.is_valid():
#                 err = _('Invalid request.')
#                 break

#             #
#             for i, file_name in enumerate([request.POST['file_name'], request.POST['file_name2']]):
#                 for info in infos:
#                     if info['name'] == file_name:
#                         if not info['status'] == 100:
#                             err = _('%(file_name)s is in importing, please wait for seconds...') % {'file_name': file_name}

#                         tmp_info = info
#                         tmp_infos.append(tmp_info)
#                         break

#                 if not tmp_info:
#                     err = _('no such file %(file_name)s') % {'file_name': file_name}
#                     break

#         if not err:
#             for i,tmp_info in enumerate(tmp_infos):
#                 tmp_risk_traits, tmp_risk_values, tmp_risk_ranks, tmp_risk_studies = get_risk_values_for_indexpage(tmp_infos[i], category=['Disease'])

#                 # Data for person A
#                 if i == 0:
#                     risk_traits = tmp_risk_traits
#                     risk_values.append(tmp_risk_values)
#                     risk_ranks.append(tmp_risk_ranks)
#                     risk_studies.append(tmp_risk_studies)

#                 # Data for person B. (Traits in chart is based on person A, so some traits are not in person B.)
#                 if i == 1:
#                     risk_values.append([])
#                     risk_ranks.append([])
#                     risk_studies.append([])

#                     for trait in risk_traits:
#                         if not trait in tmp_risk_traits:
#                             risk_values[1].append(0.0)
#                             risk_ranks[1].append('na')
#                             risk_studies[1].append('na')

#                         else:
#                             j = tmp_risk_traits.index(trait)
#                             risk_values[1].append(tmp_risk_values[j])
#                             risk_ranks[1].append(tmp_risk_ranks[j])
#                             risk_studies[1].append(tmp_risk_studies[j])

#             # Translate to Japanese
#             if browser_language == 'ja':
#                 risk_traits = [TRAITS2JA.get(trait) for trait in risk_traits]

#         break

#     return direct_to_template(request, 'risk_report/show_all.html',
#                               dict(msg=msg, err=err, infos=infos, tmp_infos=tmp_infos, do_intro=do_intro,
#                                    risk_traits=risk_traits, risk_values=risk_values, risk_ranks=risk_ranks, risk_studies=risk_studies))
