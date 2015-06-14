from django.contrib import admin
from apps.authentication.models import UserActivation, User

admin.site.register(User)
admin.site.register(UserActivation)
