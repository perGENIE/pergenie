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
                errs = form.errors.values
                break

            upload_files = request.FILES.getlist('upload_files')
            population = form.cleaned_data.get('population')
            file_format = form.cleaned_data['file_format']
            # gender = form.cleaned_data.get('gender')

            # Ensure not to exceed the limits of upload file count.
            if len(my_genomes) + len(upload_files) > settings.MAX_UPLOAD_GENOMEFILE_COUNT:
                errs.append(_('Too many files.'))
                break

            # Ensure same file is not exist.
            exists_filenames = set([x.name for x in upload_files]) & set([x['file_name'] for x in my_genomes])
            if exists_filenames:
                errs.append(_('Same file name exists. If you want to overwrite it, please delete old one.' + ' ' + ' '.join(exists_filenames)))
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
                        errs.append(_('file type not allowed, or encoding not allowed') + ': ' + upload_file.name)
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
