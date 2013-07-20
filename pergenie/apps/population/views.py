# -*- coding: utf-8 -*-

from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.utils.translation import ugettext as _
from django.conf import settings
from apps.riskreport.forms import RiskReportForm

import sys, os
# import pymongo

from utils import clogging
log = clogging.getColorLogger(__name__)


@login_required
def index(request):
    # user_id = request.user.username
    # msg, err = '', ''
    scale = 'global'  # PCA over Global 14 population, EastAsian, European, African or Americans.


    # TODO: create funciton

    # people = get_people(scale)
    # snps = get_pca_snps(scale)
    # genotyes = get_genotypes(snps)
    # person = project_new_person(genotyes, scale)

    people = [[1,2], [1,3], [2,3], [1,3]]  # points (PC1, PC2). each point represents one person.
    person = [3,3]  # one point (PC1, PC2), which represetns one person in PCA coordinate.

    return direct_to_template(request, 'population/index.html', dict(scale=scale,
                                                                     people=people,
                                                                     person=person))
