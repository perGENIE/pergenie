# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.utils.translation import ugettext as _
from django.conf import settings
from apps.riskreport.forms import RiskReportForm

import sys, os
from models import *
from lib.api.db import get_data_infos
from utils import clogging
log = clogging.getColorLogger(__name__)


@login_required
def index(request):
    user_id = request.user.username
    infos = get_data_infos(user_id)

    people = dict()
    for scale in ['global', 'EastAsia', 'Europe', 'Africa', 'Americas']:
        people[scale] = get_people(scale)
        for info in infos:
            people[scale].append(project_new_person(scale, info))

    return direct_to_template(request, 'population/index.html', dict(scale=scale,
                                                                     people=people))
