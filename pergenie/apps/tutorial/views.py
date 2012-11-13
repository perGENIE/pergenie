from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template

import pymongo

@login_required
def index(request):
    user_id = request.user.username
    msg = ''
    err = ''

    return direct_to_template(request, 'tutorial.html')
