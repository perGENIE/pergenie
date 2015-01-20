import sys
import os
import datetime

import pymongo
from pymongo_genomes import Genome, GenomeInfo, GenomeNotImportedError
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render
from django.utils import simplejson
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.conf import settings

from apps.upload.forms import UploadForm
from lib.common import clean_file_name
from lib.tasks import qimport_variants
from utils import clogging
log = clogging.getColorLogger(__name__)

try:
    import magic
    isMagicInstalled = True
except Exception:
    isMagicInstalled = False
    log.warn("==========================================================================")
    log.warn("python-magic (Filetype identification using libmagic) is not available ...")
    log.warn("==========================================================================")

@require_http_methods(['GET', 'POST'])
@login_required
def index(request):
    user_id = request.user.username

    genome_info = GenomeInfo(mongo_uri=settings.MONGO_URI)
    my_genomes = genome_info.get_infos_by_owner(user_id)

    if request.method == 'POST':
        while True:
            form = UploadForm(request.POST, request.FILES)

            if not form.is_valid():
                for err in form.errors.values():
                    messages.error(request, err)
                break

            upload_files = request.FILES.getlist('upload_files')
            population = form.cleaned_data.get('population')
            file_format = form.cleaned_data['file_format']
            # gender = form.cleaned_data.get('gender')

            # Ensure not to exceed the limits of upload file count.
            if len(my_genomes) + len(upload_files) > settings.MAX_UPLOAD_GENOMEFILE_COUNT:
                messages.error(request, _('Too many files.'))
                break

            # Ensure same file is not exist.
            exists_filenames = set([x.name for x in upload_files]) & set([x['file_name'] for x in my_genomes])
            if exists_filenames:
                messages.error(request, _('Same file name exists. If you want to overwrite it, please delete old one.' + ' ' + ' '.join(exists_filenames)))
                break

            # Ensure upload dir exists.
            tmp_upload_dir = os.path.join(settings.UPLOAD_DIR, user_id)
            if not os.path.exists(tmp_upload_dir):
                os.makedirs(tmp_upload_dir)

            for upload_file in upload_files:
                # Convert UploadedFile object to a file
                uploaded_file_path = os.path.join(tmp_upload_dir, upload_file.name)
                with open(uploaded_file_path, 'wb') as fout:
                    for chunk in upload_file.chunks():
                        fout.write(chunk)

                # Ensure the file contains the content that the content-type header claims -- "trust but verify".
                # Filetype identification using libmagic via python-magicl
                if isMagicInstalled:
                    m = magic.Magic(mime_encoding=True)
                    magic_filetype = m.from_file(uploaded_file_path)
                    log.info('magic_filetype {0}'.format(magic_filetype))
                    if not magic_filetype in ('us-ascii'):
                        messages.error(request, _('file type not allowed, or encoding not allowed') + ': ' + upload_file.name)
                        try:
                            os.remove(uploaded_file_path)
                        except OSError:
                            log.error('Could not remove invalid uploaded file')

                        continue

                # Validation passed. Upsert genome info.
                info = {'owner': user_id,
                        'file_name': upload_file.name,
                        'file_format': file_format,
                        'population': population,
                        # 'gender': gender,
                        'date': datetime.datetime.today(),
                        'status': 0.0}
                genome_info.collection.update({'owner': info['owner'], 'file_name': info['file_name']},
                                              {"$set": info}, upsert=True)

                msg = _('%(file_name)s uploaded.') % {'file_name': upload_file.name}

                # Import genome into DB as background job.
                qimport_variants.delay(info)
                msg += _(', and now importing...')

                messages.success(request, msg)

            break

    my_genomes = genome_info.get_infos_by_owner(user_id)

    return render(request, 'upload/index.html',
                  dict(uploadeds=my_genomes))


@login_required
@require_http_methods(['POST'])
def delete(request):
    file_name = request.POST.get('name')
    owner = request.user.username

    genome_info = GenomeInfo(mongo_uri=settings.MONGO_URI)
    my_genome = genome_info.get_info(owner, file_name)

    while True:
        if not my_genome:
            messages.error(request, _('Invalid request.'))
            break

        # Remove genome data.
        try:
            g = Genome(file_name, owner, mongo_uri=settings.MONGO_URI)
            g.remove()
        except GenomeNotImportedError:
            messages.error(request, _('Invalid request.'))
            break

        # Remove genome file in upload dir.
        try:
            file_path = os.path.join(settings.UPLOAD_DIR, owner, file_name)
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
    if not request.user or not request.user.username:
        result = {'status': 'error',
                  'error_message': _('login required'),
                  'uploaded_files': []}

    else:
        genome_info = GenomeInfo(mongo_uri=settings.MONGO_URI)
        my_genomes = genome_info.get_infos_by_owner(owner=request.user.username)

        result = {'status': 'ok',
                  'error_message': None,
                  'uploaded_files': {x['file_name']: x['status'] for x in my_genomes}}

    response = HttpResponse(simplejson.dumps(result), mimetype='application/json')
    response['Pragma'] = 'no-cache'
    response['Cache-Control'] = 'no-cache'

    return response
