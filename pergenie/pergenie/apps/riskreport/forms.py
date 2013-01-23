from django import forms


class RiskReportForm(forms.Form):
    file_name = forms.CharField(max_length=128)
