import uuid
import datetime

from django.db import models


class GWASCatalog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=datetime.datetime.now)
    is_active = models.BooleanField(default=False)
