from django import forms


class LibraryForm(forms.Form):
    query = forms.CharField(max_length=128)
    queries = forms.CharField(widget=forms.Textarea)
