import sys, os
from django.shortcuts import render
from django.conf import settings


def index(request):
    return render(request, 'index.html', dict())
