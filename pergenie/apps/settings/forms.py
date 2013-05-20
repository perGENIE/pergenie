from django import forms


class SettingsForm(forms.Form):
    show_level = forms.CharField(max_length=128)
    exome_ristricted = forms.BooleanField(required=False)
    use_log =  forms.BooleanField(required=False)
