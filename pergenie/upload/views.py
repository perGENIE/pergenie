from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.views.generic.simple import direct_to_template

import datetime
import os
import pymongo
import mongo.import_variants as import_variants
from upload.forms import UploadForm


@require_http_methods(['GET', 'POST'])
@login_required
def index(request):
    user_id = request.user.username
    msg = ''
    err = ''

    with pymongo.Connection() as connection:
        db = connection['pergenie']
        users = db['users']

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

                if os.path.exists(os.path.join('/tmp/pergenie', user_id, call_file.name)):
                    err = 'Same file name exists. If you want to overwrite it, please delete old one.'
                    break


                if not os.path.exists(os.path.join('/tmp/pergenie', user_id)):
                    os.mkdir(os.path.join('/tmp/pergenie', user_id))

                file_path = os.path.join('/tmp/pergenie', user_id, call_file.name)

                with open(file_path, 'wb') as fout:
                    for chunk in call_file.chunks():
                        fout.write(chunk)

                msg = 'Successfully uploaded: {}'.format(call_file.name)

                import_error_state = import_variants.import_variants(file_path, population, file_format, user_id)
                if import_error_state:
                    err = ', but import failed...' + import_error_state
                    os.remove(file_path)

                else:
                    today = str(datetime.datetime.today()).replace('-', '/')
                    data_info = {'name': call_file.name,
                                 'date': today,
                                 'population': population,
                                 'sex': sex, 'file_format':
                                 file_format}
                    users.update({'user_id': user_id}, {'$addToSet': {'data': data_info}})
                    msg += ', and imported'

                    print {'user_id': user_id}, {'$addToSet': {'data': data_info}}

                # Update user info
                # TODO: support multiple data

                # TODO
                break

        user_data = list(users.find({'user_id': user_id}))

        if not user_data:
            uploadeds = []
        elif len(user_data) > 1:
            uploadeds = 'somehow there are same user records...'
        else:
            uploadeds = user_data[0].get('data')

    return direct_to_template(request,
                              'upload.html',
                              {'msg': msg, 'err': err, 'uploadeds': uploadeds})
