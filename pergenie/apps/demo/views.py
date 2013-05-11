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


def view(request, template_name="demo.html", extra_context=None):
    # FIXME check session for OAuth token
    if client.OAUTH_KEY in request.session.keys():
        access_token = request.session[client.OAUTH_KEY]
        log.debug("user has oauth access token: %s" % access_token)
        return direct_to_template(request, template=template_name, extra_context=extra_context)
    else:
        log.debug("user doesn't have a token yet, redirect to login...")
        return redirect(client.LOGIN_URL)
