from django import forms


class RiskReportForm(forms.Form):
    genome_id = forms.UUIDField()
