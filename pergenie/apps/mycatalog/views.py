# -*- coding: utf-8 -*-
import sys, os

from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.utils import translation
from django.utils.translation import ugettext as _
from django.conf import settings
from models import *

from lib.utils.clogging import getColorLogger
log = getColorLogger(__name__)


@login_required
def index(request):
    user_id = request.user.username
    msg, err = '', ''

    mycatalog = get_mycatalog()
    for record in mycatalog:
        record['genotype_freq'], record['allele_freq'] = get_freq(record['rsid'],
                                                                  user_id)

    return direct_to_template(request, 'mycatalog/index.html',
                              dict(msg=msg, err=err,
                                   mycatalog=mycatalog
                                   ))
