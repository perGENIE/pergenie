from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.generic.simple import direct_to_template
import json
from utils.clogging import getColorLogger
log = getColorLogger(__name__)

import client  # OAuth client

def genotype(request, snpid):
    c = client.OAuthClient(request.session[client.OAUTH_KEY])
    data = c.get_genotype(snpid)
    return HttpResponse(data, mimetype="application/json")

def profiles(request):
    c = client.OAuthClient(request.session[client.OAUTH_KEY])
    data = c.get_profiles()
    return HttpResponse(data, mimetype="application/json")

def user(request):
    c = client.OAuthClient(request.session[client.OAUTH_KEY])
    data = c.get_user()
    return HttpResponse(data, mimetype="application/json")

"""
The 23andMe api calls this view with a ?code=xxxxxx paramter.  This parameter is a short lived authorization code that you must use to get a an OAuth authorization token which you can use to retrieve user data.  This view users database backed session to store the auth token instead of cookies in order to protect the token from leaving the server as it allows access to significant sensitive user information.
"""
def callback(request):
    c = client.OAuthClient()
    code = request.GET["code"]
    log.debug("code: %s" % code)

    log.debug("fetching token...")

    (access_token, refresh_token) = c.get_token(code)
    log.debug("access_token: %s refresh_token: %s" % (access_token, refresh_token))

    log.debug("refreshing token...")

    (access_token, refresh_token) = c.refresh_token(refresh_token)
    log.debug("access_token: %s refresh_token: %s" % (access_token, refresh_token))

    request.session[client.OAUTH_KEY] = access_token

    c = client.OAuthClient(request.session[client.OAUTH_KEY])
    names_json = c.get_names()
    names = json.loads(names_json)
    request.session["name"] = "%s %s" % (names['first_name'], names['last_name'])

    return redirect("/login_with_23andme/")

def logout(request):
    log.debug("logging out...")
    request.session.clear()
    return redirect("/")
