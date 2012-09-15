from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template


@login_required
def index(response):
    return direct_to_template(response, 'catalog.html')


@login_required
def catalog(response, trait):
    return direct_to_template(response, 'catalog_records.html')
