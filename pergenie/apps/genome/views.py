import sys
import os
import datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.conf import settings

import magic    # FIXME: move to .models

from .forms import UploadForm
from .models import Genome

# from lib.tasks import qimport_variants
from utils import clogging
log = clogging.getColorLogger(__name__)


@require_http_methods(['GET', 'POST'])
@login_required
def upload(request):
    if request.method == 'POST':
        while True:
            form = UploadForm(data=request.POST, files=request.FILES)

            if not form.is_valid():
                for err in form.errors.values():
                    messages.error(request, err)
                break

            upload_files = request.FILES.getlist('upload_files')

            # Ensure not to exceed the limits of upload file count.
            my_genomes = Genome.objects.filter(owners=request.user)
            if len(my_genomes) + len(upload_files) > settings.MAX_UPLOAD_GENOMEFILE_COUNT:
                messages.error(request, _('Too many files.'))
                break

            # Ensure upload dir exists.
            upload_dir = os.path.join(settings.UPLOAD_DIR, str(request.user.id))
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)

            for upload_file in upload_files:
                genome = Genome(file_name=upload_file.name,
                                display_name=upload_file.name,
                                file_format=form.cleaned_data['file_format'],
                                population=form.cleaned_data['population'],
                                sex=form.cleaned_data['sex'])

                # Convert UploadedFile object to a file
                uploaded_file_path = os.path.join(upload_dir, str(genome.id))
                with open(uploaded_file_path, 'wb+') as fout:
                    for chunk in upload_file.chunks():
                        fout.write(chunk)

                # Ensure the file contains the content that the content-type header claims -- "trust but verify".
                # Filetype identification using libmagic via python-magic
                m = magic.Magic(mime_encoding=True)
                magic_filetype = m.from_file(uploaded_file_path)
                log.info('magic_filetype {}'.format(magic_filetype))
                if not magic_filetype in ('us-ascii'):
                    messages.error(request, _('File type not allowed, or encoding not allowed. %(file_name)s' % {'file_name': file_name}))
                    try:
                        os.remove(uploaded_file_path)
                    except OSError:
                        log.error('Could not remove invalid uploaded file')

                    messages.error(request, _('Invalid request'))
                    continue

                genome.save()
                genome.owners.add(request.user)
                genome.readers.add(request.user)

                msg = _('%(file_name)s uploaded.') % {'file_name': upload_file.name}

                # Import genome into DB as background job.
                # qimport_variants.delay(info)
                # msg += _(', and now importing...')

                messages.success(request, msg)

            break

    return render(request, 'upload.html',
                  {'POPULATION_CHOICES': Genome.POPULATION_CHOICES,
                   'SEX_CHOICES': Genome.SEX_CHOICES,
                   'FILE_FORMAT_CHOICES': Genome.FILE_FORMAT_CHOICES})


@login_required
@require_http_methods(['POST'])
def delete(request):
    file_name = request.POST.get('id')
    owner = request.user.id

    while True:
        try:
            delete_target = Genome.objects.get(id=id,
                                               owners=request.user)
        except DoesNotExist:
            messages.error(request, _('Invalid request.'))
            break

        # Remove genome data.
        # from MongoDB

        # Remove genome file in upload dir.
        try:
            file_path = os.path.join(settings.UPLOAD_DIR, owner, delete_target.id)
            if os.path.exists(file_path):
                os.remove(file_path)
        except IOError:
            messages.error(request, _('Invalid request.'))
            break

        messages.success(request, _('Deleted: %(file_name)s') % {'file_name': file_name})
        break

    return redirect('apps.upload.views.index')


@login_required
def status(request):
    if not request.user:
        result = {'status': 'error',
                  'error_message': _('login required'),
                  'uploaded_files': []}

    else:
        my_genomes = Genome.objects.filter(owners=request.user)

        result = {'status': 'ok',
                  'error_message': None,
                  'uploaded_files': {x['id']: x['status'] for x in my_genomes}}

    response = JsonResponse(result)
    response['Pragma'] = 'no-cache'
    response['Cache-Control'] = 'no-cache'

    return response
