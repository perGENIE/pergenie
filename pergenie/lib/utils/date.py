from datetime import datetime

from django.utils import timezone
from django.utils.dateparse import parse_date

today = timezone.now().strftime('%Y-%m-%d')
current_tz = timezone.get_current_timezone()
today_with_tz = current_tz.localize(datetime(*(parse_date(today).timetuple()[:5])))
