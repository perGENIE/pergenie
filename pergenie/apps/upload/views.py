import sys
import os
import datetime

import pymongo
from pymongo_genomes import GenomeInfo
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.shortcuts import redirect, render
from django.utils import simplejson
from django.views.decorators.http import require_http_methods
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
    msg, err, msgs, errs = '', '', [], []

    if user_id.startswith(settings.DEMO_USER_ID):
        raise Http404

    genome_info = GenomeInfo(mongo_uri=settings.MONGO_URI)
    my_genomes = genome_info.get_infos_by_owner(user_id)

    if request.method == 'POST':
        while True:
            form = UploadForm(request.POST, request.FILES)

            if not form.is_valid():
                err = _('Invalid request')
                break

            call_files = request.FILES.getlist('call')
            population = form.cleaned_data.get('population')
            # gender = form.cleaned_data.get('gender')
            file_format = form.cleaned_data['file_format']

            # TODO: migrate validations to form.py

            # Validate: Forms are filled with valid value
            if not call_files:
                err = _('Select data file.')
                break

            if not population or population not in ('unknown', 'Asian', 'European', 'Japanese'):
                err = _('Select population.')
                break

            fileformats = [x['name'] for x in settings.FILEFORMATS]
            if not file_format or file_format not in fileformats:
                err = _('Select file format.')
                break

            if len(call_files) > settings.UPLOAD_GENOMEFILE_COUNT:
                err = _('Too many files.')
                break

            if len(my_genomes) + len(call_files) > settings.UPLOAD_GENOMEFILE_COUNT:
                err = _('Too many files.')
                break

            # Validate: Uploaded file is valid
            for call_file in call_files:
                if call_file.size > settings.UPLOAD_GENOMEFILE_SIZE_LIMIT:
                    errs.append(_('too large file size') + ': ' + call_file.name)
                    continue

                call_file_ext = os.path.splitext(call_file.name)[1].lower()[1:]

                if call_file_ext not in ('csv', 'txt', 'vcf'):
                    errs.append(_('file extension not allowed') + ': ' + call_file.name)
                    continue

                log.debug('content_type: {0}'.format(call_file.content_type))

                if call_file.content_type == 'text/plain':
                    pass
                elif call_file.content_type in ('text/directory', 'text/vcard') and call_file_ext == 'vcf':
                    pass
                else:
                    errs.append(_('file type not allowed') + ': ' + call_file.name)
                    continue

                # Still need to validate that the file contains the content that the content-type header claims -- "trust but verify".

                # # Ensure same file is not exist.
                # if True in [x['file_name'] == call_file.name for x in my_genomes]:
                #     errs.append(_('Same file name exists. If you want to overwrite it, please delete old one.') + ': ' + call_file.name)
                #     continue

                # Ensure upload dir exists.
                tmp_upload_dir = os.path.join(settings.UPLOAD_DIR, user_id)
                if not os.path.exists(tmp_upload_dir):
                    os.makedirs(tmp_upload_dir)

                # Convert UploadedFile object to a filel
                uploaded_file_path = os.path.join(tmp_upload_dir, call_file.name)
                with open(uploaded_file_path, 'wb') as fout:
                    for chunk in call_file.chunks():
                        fout.write(chunk)

                # Filetype identification using libmagic via python-magicl
                if isMagicInstalled:
                    m = magic.Magic(mime_encoding=True)
                    magic_filetype = m.from_file(uploaded_file_path)
                    log.debug('magic_filetype {0}'.format(magic_filetype))
                    if not magic_filetype in ('us-ascii'):
                        errs.append(_('file type not allowed, or encoding not allowed') + ': ' + call_file.name)
                        try:
                            os.remove(uploaded_file_path)
                        except OSError:
                            log.debug('[ERROR] could not remove invalid uploaded file')

                        continue

                info = {'owner': user_id,
                        'file_name': call_file.name,
                        'file_format': file_format,
                        'population': population,
                        'gender': gender,
                        'date': datetime.datetime.today(),
                        'status': 0.0}
                genome_info.collection.update({'owner': info['owner'], 'file_name': info['file_name']},
                                              {"$set": info}, upsert=True)

                msg = _('%(file_name)s uploaded.') % {'file_name': call_file.name}

                # Run background job: Import genome into DB
                qimport_variants.delay(info)
                msg += _(', and now importing...')

                msgs.append(msg)
                msg = ''

            break

    my_genomes = genome_info.get_infos_by_owner(user_id)

    return render(request, 'upload/index.html',
                  dict(msg=msg, err=err, msgs=msgs, errs=errs, uploadeds=my_genomes))


@login_required
def delete(request):
    user_id = request.user.username

    if user_id.startswith(settings.DEMO_USER_ID):
        raise Http404

    name = request.POST.get('name')

    with pymongo.MongoClient(host=settings.MONGO_URI) as connection:
        db = connection['pergenie']
        data_info = db['data_info']

        # delete Mongo Collection
        target_collection = genomes.get_variants(user_id, name).name
        log.debug(target_collection)

        log.debug('target is in db {0}'.format(target_collection in db.collection_names()))
        db.drop_collection(target_collection)
        log.debug('target is in db {0}'.format(target_collection in db.collection_names()))

        # delete `file`
        tmp_data_info = data_info.find_one({'user_id': user_id, 'name': name})
        if tmp_data_info:
            filepath = os.path.join(settings.UPLOAD_DIR,
                                    user_id,
                                    tmp_data_info['file_format'],
                                    tmp_data_info['raw_name'])
            if os.path.exists(filepath):
                os.remove(filepath)

        # delete document `data_info`
        if data_info.find_one({'user_id': user_id, 'name': name}):
            data_info.remove({'user_id': user_id, 'name': name})

    return redirect('apps.upload.views.index')


@login_required
def status(request):
    if not request.user or not request.user.username:
        result = {'status': 'error',
                  'error_message': 'login required',
                  'uploaded_files': []}

    else:
        user_id = request.user.username

        if user_id.startswith(settings.DEMO_USER_ID):
            raise Http404

        with pymongo.MongoClient(host=settings.MONGO_URI) as connection:
            db = connection['pergenie']
            data_info = db['data_info']

            uploaded_files = {}
            for record in data_info.find({'user_id': user_id}):
                uploaded_files[record['name']] = record['status']

        result = {'status': 'ok',
                  'error_message': None,
                  'uploaded_files': uploaded_files}

    response = HttpResponse(simplejson.dumps(result), mimetype='application/json')
    response['Pragma'] = 'no-cache'
    response['Cache-Control'] = 'no-cache'

    return response
