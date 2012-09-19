from django import forms


class CatalogForm(forms.Form):
    query = forms.CharField(max_length=128)
