from django import forms

class UploadForm(forms.Form):

    # no limit for filename max_length
    # not allow_empty_file
    call = forms.FileField()

    population = forms.CharField(max_length=128)
    sex = forms.CharField(max_length=128)
    file_format = forms.CharField(max_length=128)
