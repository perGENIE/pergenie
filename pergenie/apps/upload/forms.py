from django import forms


class UploadForm(forms.Form):
    call = forms.FileField()
    population = forms.CharField(max_length=128)
    sex = forms.CharField(max_length=128)
    file_format = forms.CharField(max_length=128)
