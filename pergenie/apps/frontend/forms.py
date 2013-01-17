from django import forms
# from django.utils.translation import ugettext as _
# from django.conf import settings


class LoginForm(forms.Form):
    user_id = forms.EmailField(max_length=128)
    password = forms.CharField(max_length=128)


class RegisterForm(forms.Form):
    user_id = forms.EmailField(max_length=128)
    password1 = forms.CharField(max_length=128)
    password2 = forms.CharField(max_length=128)

    # def clean_password(self):
    #     password1 = self.cleaned_data.get('password1')
    #     password2 = self.cleaned_data.get('password2')

    #     if password1 != password2:
    #         raise forms.ValidationError(_('Passwords do not match.'))

    #     password = password1
    #     if len(password) < settings.MIN_PASSWORD_LENGTH:
    #         raise forms.ValidationError('Password too short')

    #     return super(RegisterForm, self).clean_password()
