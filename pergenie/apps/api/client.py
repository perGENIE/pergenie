import requests
# Get the token using a POST request and a code

from django.conf import settings

SCOPE = settings.SCOPE

# leave these alone
BASE_URL = "https://api.23andme.com/1/demo/"
LOGIN_URL = "https://api.23andme.com/authorize/?redirect_uri=%s&response_type=code&client_id=%s&scope=%s" % (settings.CALLBACK_URL, settings.CLIENT_ID, SCOPE)
OAUTH_KEY = "access_token"


class OAuthClient(object):
    def __init__(self, access_token=None):
        self.access_token = access_token

    def get_token(self, authorization_code):
        parameters = {
            'client_id': settings.CLIENT_ID,
            'client_secret': settings.CLIENT_SECRET,
            'grant_type': 'authorization_code',
            'code': authorization_code, # the authorization code obtained above
            'redirect_uri': settings.CALLBACK_URL,
            'scope': SCOPE,
        }
        response = requests.post(
            "https://api.23andme.com/token/",
            data = parameters
        )

        print "response.json: %s" % response.json()
        if response.status_code == 200:
            return (response.json()['access_token'], response.json()['refresh_token'])
        else:
            response.raise_for_status()

    def refresh_token(self, refresh_token):
        parameters = {
            'client_id': settings.CLIENT_ID,
            'client_secret': settings.CLIENT_SECRET,
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
            'redirect_uri': settings.CALLBACK_URL,
            'scope': SCOPE,
        }
        response = requests.post(
            "https://api.23andme.com/token/",
            data = parameters
        )

        print "response.json: %s" % response.json()
        if response.status_code == 200:
            self.access_token = response.json()['access_token']
            return (response.json()['access_token'], response.json()['refresh_token'])
        else:
            response.raise_for_status()

    def _get_resource(self, resource):
        if self.access_token is None:
            raise Exception("access_token cannot be None")

        headers = {'Authorization': 'Bearer %s' % self.access_token}
        url = "%s%s" % (BASE_URL, resource)
        response = requests.get(
            url,
            headers=headers,
            verify=False,
        )
        print "url: %s" % url
        print "response: %s" % response
        print "response.json: %s" % response.json()
        print "response.text: %s" % response.text
        if response.status_code == 200:
            return response.text
        else:
            response.raise_for_status()

    def get_user(self):
        return self._get_resource("user/")

    def get_names(self):
        return self._get_resource("names/")

    def get_profiles(self):
        return self._get_resource("profiles/")

    def get_genotype(self, locations):
        return self._get_resource("genotypes/?locations=%s" % locations)
