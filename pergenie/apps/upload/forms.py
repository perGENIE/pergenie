import os

from django import forms
from django.utils.translation import ugettext as _
from django.conf import settings

class UploadForm(forms.Form):
    upload_files = forms.FileField(
        max_length=128,
        error_messages={'required': _('Select data file.'),
                        'max_length': _('Too long file name')}
    )

    population = forms.ChoiceField(
        (('unknown', 'unknown'),
         ('Asian', 'Asian'),
         ('European', 'European'),
         ('Japanese', 'Japanese')),
        error_messages={'required': _('Select population.'),
                        'invalid_choice': _('Select population.')}
    )

    _fileformats = [x['name'] for x in settings.FILEFORMATS]
    file_format = forms.ChoiceField(
        zip(_fileformats, _fileformats),
        error_messages={'required': _('Select file format.'),
                        'invalid_choice': _('Select file format.')}
    )

    # gender = forms.ChoiceField()

    def clean_upload_files(self):
        upload_files = self.files.getlist('upload_files')

        for upload_file in upload_files:
            if len(upload_file.name) > settings.MAX_UPLOAD_GENOMEFILE_NAME_LENGTH:
                raise forms.ValidationError(_('Too long file name.'))

            if upload_file.size > settings.MAX_UPLOAD_GENOMEFILE_SIZE:
                raise forms.ValidationError(_('Too large file size: %(file_name)s' % {'file_name': upload_file.name}))

            ext = os.path.splitext(upload_file.name)[1].lower()[1:]
            if ext not in ('csv', 'txt', 'vcf'):
                raise forms.ValidationError(_('Not allowed file extention: %(file_name)s' % {'file_name': upload_file.name}))

            if upload_file.content_type == 'text/plain':
                pass
            elif upload_file.content_type in ('text/directory', 'text/vcard') and ext == 'vcf':
                pass
            else:
                raise forms.ValidationError(_('Not allowed file type: %(file_name)s' % {'file_name': upload_file.name}))

        return upload_files
