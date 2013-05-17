from django.views.generic.simple import direct_to_template
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.shortcuts import redirect, render
from django.core.mail import mail_admins
from django.conf import settings

from apps.api import client

from utils.clogging import getColorLogger
log = getColorLogger(__name__)

# SCOPE_RS_LIST = ["rs53576", "rs1815739", "rs6152", "rs1800497", "rs1805007", "rs9939609", "rs662799", "rs7495174", "rs7903146", "rs12255372", "rs1799971", "rs17822931", "rs4680", "rs1333049", "rs1801133", "rs1051730", "rs3750344", "rs4988235"]


def view(request):
    # FIXME check session for OAuth token
    if client.OAUTH_KEY in request.session.keys():
        access_token = request.session[client.OAUTH_KEY]
        log.debug("user has oauth access token: %s" % access_token)

        c = client.OAuthClient(request.session[client.OAUTH_KEY])

        user_info = c.get_user()
        user_genotypes = {}

        for rsid in setting.SCOPE_RS_LIST[0:4]:
            try:
                user_genotypes[rsid] = c.get_genotype(rsid)
            except:
                # if external SCOPE, get `400 Client Error: Bad Request`
                user_genotypes[rsid] = u'[]'

        return direct_to_template(request, "demo.html",
                                  dict(user_info=user_info,
                                       user_genotypes=user_genotypes))

    else:
        log.debug("user doesn't have a token yet, redirect to login...")
        return redirect(client.LOGIN_URL)
