from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.http import Http404
from django.utils.translation import ugettext as _
from django.conf import settings
from apps.riskreport.forms import RiskReportForm

import sys, os
import re

from models import *

from utils import clogging
log = clogging.getColorLogger(__name__)


@login_required
def index(request):
    user_id = request.user.username
    msg, err = '', ''

    # pdb_name = '3SXE'
    # pdb_records = pdb2var(pdb_name)

    return direct_to_template(request, 'myprotain/index.html',
                              dict())
                              # dict(pdb_records=pdb_records,
                              #      pdb_name=pdb_name))

@login_required
def my_pdb(request, pdb_id):
    user_id = request.user.username
    msg, err = '', ''

    # TODO:
    # if not pdb_id in pdb_ids:
    #     raise Http404

    # pdb_id_info = get_my_pdb_id(pdb_id)
    pdb_records = pdb2var(pdb_id)
    pdb_name = pdb_id.upper()

    return direct_to_template(request, 'myprotain/pdb.html',
                              dict(pdb_records=pdb_records,
                                   pdb_name=pdb_name))
