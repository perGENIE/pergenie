from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.conf import settings

from .models import *
from utils import clogging
log = clogging.getColorLogger(__name__)


@login_required
def index(request):
    user_id = request.user.username

    people = dict()
    scales = ['global']  # ['global', 'EastAsia', 'Europe', 'Africa', 'Americas']
    for scale in scales:
        people[scale] = get_people(scale)
        for info in infos:
            people[scale].append(project_new_person(scale, info))

    context =  dict(scale=scale,
                    people=people)

    return render(request, 'population/index.html',
                  context)
