import sys, os
from django.shortcuts import redirect
from django.views.generic.simple import direct_to_template
from django.conf import settings


def index(request):
    return direct_to_template(request, 'index.html', dict())
