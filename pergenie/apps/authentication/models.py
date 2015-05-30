from datetime import datetime

from django.db import models
from django.contrib.auth.models import User

class UserActivation(models.Model):
    user = models.OneToOneField(User)
    activation_key = models.CharField(max_length=40, unique=True)
    created_at = models.DateTimeField(default=datetime.now)
