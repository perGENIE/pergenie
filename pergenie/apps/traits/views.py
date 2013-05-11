# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
# from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template
from django.utils.translation import ugettext as _
from django.conf import settings
from apps.riskreport.forms import RiskReportForm

import sys, os
import pymongo

from lib.mongo.get_latest_catalog import get_latest_catalog
from lib.mongo.get_traits_infos import get_traits_infos
from utils import clogging
log = clogging.getColorLogger(__name__)

# TRAITS, TRAITS2JA, TRAITS2CATEGORY, TRAITS2WIKI_URL_EN = get_traits_infos(as_dict=True)
# JA2TRAITS = dict([(v, k) for (k, v) in TRAITS2JA.items()])


# @require_http_methods(['GET', 'POST'])
@login_required
def index(request):
    user_id = request.user.username
    msg, err = '', ''

    return direct_to_template(request, 'traits/index.html', {})
