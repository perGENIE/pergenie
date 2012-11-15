# -*- coding: utf-8 -*- 

from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template

import pymongo

@login_required
def index(request):
    user_id = request.user.username
    msg = ''
    err = ''

    with pymongo.Connection() as connection:
        db = connection['pergenie']
        data_info = db['data_info']

        while True:
            # determine file
            infos = list(data_info.find( {'user_id': user_id} ))

            if not infos:
                msg = 'まずは，genome fileをアップロードしましょう!'
                break

    return direct_to_template(request,
                              'dashboard.html',
                              {'msg': msg, 'err': err})
