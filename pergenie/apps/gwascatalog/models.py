import uuid
import datetime

from django.db import models
from django.conf import settings
from django.utils.translation import ugettext as _

from pergenie.mongo import mongo_db
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class GWASCatalog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=datetime.datetime.now)
    is_active = models.BooleanField(default=False)

    def get_catalog(self):
        return mongo_db['gwascatalog-' + str(self.id)]

    def delete_catalog(self):
        mongo_db.drop_collection(self.get_catalog())
