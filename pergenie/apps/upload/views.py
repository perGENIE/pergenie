from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils import simplejson
from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template

import datetime
import os
import pymongo
from lib.tasks import qimport_variants
from apps.upload.forms import UploadForm

UPLOAD_DIR = '/tmp/pergenie'

@require_http_methods(['GET', 'POST'])
@login_required
def index(request):
    user_id = request.user.username
    msg = ''
    err = ''

    with pymongo.Connection() as connection:
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

                if not call_file:
                    err = 'Select data file.'
                    break

                if not population:
                    err = 'Select population.'
                    break

                print call_file.name
                if os.path.splitext(call_file.name)[1].lower()[1:] not in ('csv', 'txt', 'vcf'):
                    err = 'Not allowed file extension.'
                    break

                if data_info.find({'user_id': user_id, 'name': call_file.name}).count() > 0:
                    err = 'Same file name exists. If you want to overwrite it, please delete old one.'
                    break


                if not os.path.exists(os.path.join(UPLOAD_DIR, user_id)):
                    os.makedirs(os.path.join(UPLOAD_DIR, user_id))

                with open(os.path.join(UPLOAD_DIR, user_id, call_file.name), 'wb') as fout:
                    for chunk in call_file.chunks():
                        fout.write(chunk)

                msg = 'Successfully uploaded: {}'.format(call_file.name)

                today = str(datetime.datetime.today()).replace('-', '/')
                info = {'user_id': user_id,
                        'name': call_file.name,
                        'date': today,
                        'population': population,
                        'sex': sex,
                        'file_format': file_format,
                        'status': float(0.0)}
                data_info.insert(info)

                # TODO: Throw queue
                qimport_variants.delay(info)
                msg += ', and now importing. (sorry, it takes for minutes...)'

                print '[INFO] data_info:', info

                # TODO: support multiple data

                # TODO
                break

        uploadeds = list(data_info.find( {'user_id': user_id} ))

    return direct_to_template(request,
                              'upload.html',
                              {'msg': msg, 'err': err, 'uploadeds': uploadeds})


@login_required
def delete(request):
    user_id = request.user.username
    name = request.GET.get('name')

    with pymongo.Connection() as connection:
        db = connection['pergenie']
        data_info = db['data_info']
        variant = db['variant']

        # TODO: prohibit removal while importing is in operation
        if data_info.find({'user_id': user_id, 'name': name})[0]['status']:
            data_info.remove({'user_id': user_id, 'name': name})

    return redirect('apps.upload.views.index')


def status(request):
    if not request.user or not request.user.username:
        result = {'status': 'error',
                  'error_message': 'login required',
                  'uploaded_files': []}

    else:
        user_id = request.user.username


        with pymongo.Connection() as connection:
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
