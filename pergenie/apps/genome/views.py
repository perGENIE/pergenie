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

import magic

from .forms import UploadForm
from .models import Genome
from apps.authentication.models import User

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
            my_genomes = Genome.objects.filter(owner=request.user)
            if len(my_genomes) + len(upload_files) > settings.MAX_UPLOAD_GENOMEFILE_COUNT:
                messages.error(request, _('Too many files.'))
                break

            # Ensure upload dir exists.
            upload_dir = os.path.join(settings.UPLOAD_DIR, str(request.user.id))
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)

            for upload_file in upload_files:
                genome = Genome(owner=request.user,
                                file_name=upload_file.name,
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

                if not magic_filetype in ('us-ascii'):
                    msg = _('File type not allowed, or encoding not allowed {magic_filetype}: {file_name}'.format(file_name=file_name, magic_filetype=magic_filetype))
                    log.warn(msg)
                    messages.error(request, msg)
                    try:
                        os.remove(uploaded_file_path)
                    except OSError:
                        log.error('Could not remove invalid uploaded file')

                    messages.error(request, _('Invalid request'))
                    continue

                genome.save()
                genome.readers.add(request.user)

                msg = _('%(file_name)s uploaded.') % {'file_name': upload_file.name}

                # Import genome into DB as background job.
                genome.create_genotypes()
                msg += _(', and now importing...')

                messages.success(request, msg)

            break

    user = User.objects.filter(id=request.user.id)

    owner_genomes = Genome.objects.filter(owner=user)
    reader_genomes = Genome.objects.filter(readers__in=user)
    my_genomes = list(owner_genomes) + list(reader_genomes)

    return render(request, 'upload.html',
                  {'POPULATION_CHOICES': Genome.POPULATION_CHOICES,
                   'SEX_CHOICES': Genome.SEX_CHOICES,
                   'FILE_FORMAT_CHOICES': Genome.FILE_FORMAT_CHOICES,
                   'my_genomes': my_genomes})


@login_required
@require_http_methods(['POST'])
def delete(request):
    genome_id = request.POST.get('id')

    try:
        genome = Genome.objects.get(owner=request.user, id=genome_id)

        genome.delete_genotypes()

        file_path = genome.get_genome_file()
        if os.path.exists(file_path):
            os.remove(file_path)

        genome.delete()

        messages.success(request, _('Deleted: {}'.format(genome.file_name)))

    except DoesNotExist:
        log.error('Failed to delete not existing genome: {}'.format(genome_id))
        messages.error(request, _('Invalid request.'))
    except IOError:
        log.error('Failed to delete not existing file: {}'.format(file_path))
        messages.error(request, _('Invalid request.'))

    return redirect('genome-upload')


@login_required
def status(request):
    if not request.user:
        result = {'status': 'error',
                  'error_message': _('login required'),
                  'genome_info': []}

    else:
        my_genomes = Genome.objects.filter(owner=request.user)
        result = {'status': 'ok',
                  'error_message': '',
                  'genome_info': {str(x.id): x.status for x in my_genomes}}

    response = JsonResponse(result)
    response['Pragma'] = 'no-cache'
    response['Cache-Control'] = 'no-cache'

    return response
