from django import forms
from django.conf import settings
from django.utils.translation import ugettext as _


class LoginForm(forms.Form):
    email = forms.EmailField(max_length=254)
    password = forms.CharField(max_length=1024)


class RegisterForm(forms.Form):
    email = forms.EmailField(max_length=254)
    password1 = forms.CharField(max_length=1024)
    password2 = forms.CharField(max_length=1024)
    terms_ok_0 = forms.BooleanField(required=False)
    terms_ok_1 = forms.BooleanField(required=False)

    def clean(self):
        cleaned_data = super(RegisterForm, self).clean()

        email = cleaned_data.get('email')
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        terms_ok_0 = cleaned_data.get('terms_ok_0')
        terms_ok_1 = cleaned_data.get('terms_ok_1')

        # TODO: too weak password
        if password1:
            if len(password1) < int(settings.MIN_PASSWORD_LENGTH):
                msg = _('Passwords too short (passwords should be longer than %(min_password_length)s characters).' % {'min_password_length': settings.MIN_PASSWORD_LENGTH})
                self.add_error('password1', msg)

        if password1 and password2:
            if password1 != password2:
                msg = _('Passwords do not match.')
                self.add_error('password2', msg)

        if not terms_ok_0 or not terms_ok_1:
            msg = _('Not read and accept about service of perGENIE.')
            self.add_error('terms_ok_0', msg)
            self.add_error('terms_ok_1', msg)
