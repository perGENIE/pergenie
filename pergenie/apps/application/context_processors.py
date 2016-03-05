from django.conf import settings

def google_analytics(request):
    ga_property_id = getattr(settings, 'GOOGLE_ANALYTICS_PROPERTY_ID', '')

    if ga_property_id and not settings.DEBUG:
        context = {'GOOGLE_ANALYTICS_PROPERTY_ID': ga_property_id}
    else:
        context = {}

    return context
