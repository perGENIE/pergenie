# -*- coding: utf-8 -*- 

from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template

import pymongo

from django.conf import settings

@login_required
def index(request):
    user_id = request.user.username
    msg = ''
    err = ''

    with pymongo.Connection(port=settings.MONGO_PORT) as connection:
        db = connection['pergenie']
        data_info = db['data_info']

        latest_document = db['catalog_info'].find_one({'status': 'latest'})
        if latest_document:
            latest_date = str(latest_document['date'].date()).replace('-', '_')
        else:
            # TODO: error handling
            latest_date = None
            err = 'latest catalog does not exist!'

        while True:
            # determine file
            infos = list(data_info.find( {'user_id': user_id} ))

            if not infos:
                msg = 'まずは，genome fileをアップロードしましょう!'
                break

            break

    return direct_to_template(request,
                              'dashboard.html',
                              {'msg': msg, 'err': err,
                               'catalog_latest_date': latest_date})
