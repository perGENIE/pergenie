from django import forms


class SettingsForm(forms.Form):
    show_level = forms.CharField(max_length=128)

