from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _

from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class GwasCatalog(models.Model):
    pass
