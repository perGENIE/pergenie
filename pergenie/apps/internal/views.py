from django.http import JsonResponse

from utils import clogging
log = clogging.getColorLogger(__name__)


def health_check(request):
    return JsonResponse({'status': 'ok'})
