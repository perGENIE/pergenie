# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.http import Http404
from django.utils.translation import ugettext as _
from django.conf import settings
from apps.riskreport.forms import RiskReportForm

# import sys, os
# import pymongo

# from lib.mongo.get_latest_catalog import get_latest_catalog
# from lib.mongo.get_traits_infos import get_traits_infos
from models import *

from utils import clogging
log = clogging.getColorLogger(__name__)


@login_required
def index(request):
    user_id = request.user.username
    msg, err = '', ''

    pdb_name = '3SXE'
    pdb_records = pdb2var(pdb_name)

    return direct_to_template(request, 'myprotain/index.html',
                              dict(pdb_records=pdb_records,
                                   pdb_name=pdb_name))
