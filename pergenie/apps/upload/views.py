# -*- coding: utf-8 -*- 

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import simplejson
from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template
from django.conf import settings
from apps.upload.forms import UploadForm

import datetime
import os
import pymongo
import magic
from lib.tasks import qimport_variants
from utils import clogging
log = clogging.getColorLogger(__name__)


@require_http_methods(['GET', 'POST'])
@login_required
def index(request):
    user_id = request.user.username
    msg = ''
    err = ''

    with pymongo.Connection(port=settings.MONGO_PORT) as connection:
        db = connection['pergenie']
        data_info = db['data_info']

        if request.method == 'POST':
            while True:
                form = UploadForm(request.POST, request.FILES)

                if not form.is_valid():
                    err = 'Invalid request'
                    break

                call_file = request.FILES['call']
                population = form.cleaned_data['population']
                sex = form.cleaned_data['sex']
                file_format = form.cleaned_data['file_format']


                """Security: validate that forms are filled with valid value"""

                if not call_file:  # TODO: ok?
                    err = 'ファイルを選択して下さい．'
                    # err = 'Select data file.'
                    break

                if not population or population not in ('unknown', 'Asian', 'Europian', 'Japanese'):
                    err = 'Populationを選択して下さい．'
                    # err = 'Select population.'
                    break

                if not sex or sex not in ('unknown', 'male', 'female'):
                    err = 'Sexを選択して下さい．'
                    break

                if not file_format or file_format not in ('andme', 'navi', 'vcf', 'tmmb'):
                    err = 'File Formatを選択して下さい．'
                    break


                """Security: validate that uploaded file is valid"""

                if call_file.size > settings.UPLOAD_GENOMEFILE_SIZE_LIMIT:
                    err = 'ファイルサイズが制限を超えています．'
                    break

                if not call_file.content_type == 'text/plain':
                    err = '許可されていないファイルタイプです．'

                # still need to validate that the file contains the content that the content-type header claims -- "trust but verify."

                if os.path.splitext(call_file.name)[1].lower()[1:] not in ('csv', 'txt', 'vcf'):
                    err = '許可されいてない拡張子のファイルです．'
                    # err = 'Not allowed file extension.'
                    break

                if data_info.find({'user_id': user_id, 'raw_name': call_file.name}).count() > 0:
                    err = '同じファイル名のファイルがアップロードされています．上書きしたい場合，アップロード済みのファイルを削除して下さい．'
                    # err = 'Same file name exists. If you want to overwrite it, please delete old one.'
                    break

                if not os.path.exists(os.path.join(settings.UPLOAD_DIR, user_id)):
                    os.makedirs(os.path.join(settings.UPLOAD_DIR, user_id))

                # convert UploadedFile object to a file
                uploaded_file_path = os.path.join(settings.UPLOAD_DIR, user_id, call_file.name)
                with open(uploaded_file_path, 'wb') as fout:
                    for chunk in call_file.chunks():
                        fout.write(chunk)

                # filetype identification using libmagic via python-magic
                m = magic.Magic(mime_encoding=True)
                magic_filetype = m.from_file(uploaded_file_path)
                if not magic_filetype in ('us-ascii'):
                    err = '許可されていないファイルタイプ，あるいは許可されていないエンコーディングです．'
                    log.debug('magic_filetype {}'.format(magic_filetype))
                    try:
                        os.remove(uploaded_file_path)
                    except OSError:
                        log.debug('[ERROR] could not remove invalid uploaded file')
                    
                    break

                msg = '{}がアップロードされました．'.format(call_file.name)
                log.debug('uploaded_file_path: {}'.format(uploaded_file_path))
                # msg = 'Successfully uploaded: {}'.format(call_file.name)

                # TODO: check if clery is alive
                
                today = str(datetime.datetime.today()).replace('-', '/')
                file_name_cleaned = call_file.name.replace('.', '').replace(' ', '')

                info = {'user_id': user_id,
                        'name': file_name_cleaned,
                        'raw_name': call_file.name,
                        'date': today,
                        'population': population,
                        'sex': sex,
                        'file_format': file_format,
                        'status': float(0.0)}
                data_info.insert(info)

                qimport_variants.delay(info)
                msg += '現在，読み込んでいます...'
                # msg += ', and now importing...'

                break

        uploadeds = list(data_info.find( {'user_id': user_id} ))
    
    if err:
        log.error('UPLOAD err: {}')
    return direct_to_template(request, 'upload.html',
                              {'msg': msg, 'err': err, 'uploadeds': uploadeds})


@login_required
def delete(request):
    user_id = request.user.username
    name = request.POST.get('name')

    with pymongo.Connection(port=settings.MONGO_PORT) as connection:
        db = connection['pergenie']
        data_info = db['data_info']
        variant = db['variant']

        log.info('data_info.find(): {})'.format(list(data_info.find())))
        log.info('user_id: {0} name: {1}'.format(user_id, name))

        if data_info.find_one({'user_id': user_id, 'name': name}):
            data_info.remove({'user_id': user_id, 'name': name})
            
        #
        users_variants = db['variants'][user_id][data_info['file_name_cleaned']]
        db.drop_collection(users_variants)
        log.debug('dropped ccollection {}'.format(users_variants))

    return redirect('apps.upload.views.index')

@login_required
def status(request):
    if not request.user or not request.user.username:
        result = {'status': 'error',
                  'error_message': 'login required',
                  'uploaded_files': []}

    else:
        user_id = request.user.username


        with pymongo.Connection(port=settings.MONGO_PORT) as connection:
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
