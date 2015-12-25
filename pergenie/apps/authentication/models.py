from uuid import uuid4

from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.core.mail import send_mail
from django.core import validators
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.conf import settings


class UserManager(BaseUserManager):
    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password, **extra_fields):
        user = self.create_user(username, email, password=password, **extra_fields)
        user.is_active = True
        user.is_admin = True
        user.save(using=self._db)
        return user


class UserGrade(models.Model):
    name = models.CharField(max_length=20, unique=True, default='default')


class User(AbstractBaseUser):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    username = models.CharField(_('username'), max_length=128, unique=True,
                                help_text=_('Required. 128 characters or fewer. Letters, digits and '
                                            '@/./+/-/_ only.'),
                                validators=[
                                    validators.RegexValidator(r'^[\w.@+-]+$',
                                                              _('Enter a valid username. '
                                                                'This value may contain only letters, numbers '
                                                                'and @/./+/-/_ characters.'), 'invalid'),
                                ],
                                error_messages={
                                    'unique': _("A user with that username already exists."),
                                })
    email = models.EmailField(_('email address'), max_length=254, unique=True)
    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_demo = models.BooleanField(default=False)
    grade = models.ForeignKey(UserGrade)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    _demo_name = 'demo@{}'.format(settings.DOMAIN)

    def get_full_name(self):
        return self._demo_name if self.is_demo else self.email

    def get_short_name(self):
        return self._demo_name if self.is_demo else self.email

    def __str__(self):
        return self._demo_name if self.is_demo else self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin

    def email_user(self, subject, message, from_email=None):
        send_mail(subject, message, from_email, [self.email])


class UserActivation(models.Model):
    user = models.OneToOneField(User)
    activation_key = models.CharField(max_length=40, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
