from django import forms


class LoginForm(forms.Form):
    user_id = forms.EmailField(max_length=128)
    password = forms.CharField(max_length=128)


class RegisterForm(forms.Form):
    user_id = forms.EmailField(max_length=128)
    password1 = forms.CharField(max_length=128)
    password2 = forms.CharField(max_length=128)
