import os

from django import forms
from django.utils.translation import ugettext as _
from django.conf import settings

from .models import Genome


class UploadForm(forms.Form):
    upload_files = forms.FileField(
        max_length=100,
        error_messages={'required': _('Select data file.'),
                        'max_length': _('Too long file name')}
    )

    population = forms.ChoiceField(
        Genome.POPULATION_CHOICES,
        error_messages={'required': _('Select population.'),
                        'invalid_choice': _('Select population.')}
    )

    file_format = forms.ChoiceField(
        Genome.FILE_FORMAT_CHOICES,
        error_messages={'required': _('Select file format.'),
                        'invalid_choice': _('Select file format.')}
    )

    sex = forms.ChoiceField(
        Genome.SEX_CHOICES,
        error_messages={'required': _('Select file format.'),
                        'invalid_choice': _('Select file format.')}
    )

    def clean_upload_files(self):
        upload_files = self.files.getlist('upload_files')

        for upload_file in upload_files:
            if len(upload_file.name) > settings.MAX_UPLOAD_GENOME_FILE_NAME_LENGTH:
                raise forms.ValidationError(_('Too long file name.'))

            if upload_file.size > settings.MAX_UPLOAD_GENOME_FILE_SIZE:
                raise forms.ValidationError(_('Too large file size: %(file_name)s' % {'file_name': upload_file.name}))

            ext = os.path.splitext(upload_file.name)[1].lower()[1:]
            if ext not in ('csv', 'txt', 'vcf', 'tsv'):
                raise forms.ValidationError(_('Not allowed file extention: %(file_name)s' % {'file_name': upload_file.name}))

            if upload_file.content_type == 'text/plain':
                pass
            elif upload_file.content_type in ('text/directory', 'text/vcard') and ext == 'vcf':
                pass
            else:
                raise forms.ValidationError(_('Not allowed file type: %(file_name)s' % {'file_name': upload_file.name}))

        return upload_files
