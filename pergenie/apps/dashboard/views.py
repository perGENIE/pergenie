# -*- coding: utf-8 -*- 

from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.conf import settings

import datetime
import pymongo

from utils.date import today_date, today_str

@login_required
def index(request):
    user_id = request.user.username
    msg = ''
    err = ''

    with pymongo.Connection(port=settings.MONGO_PORT) as connection:
        db = connection['pergenie']
        catalog_info = db['catalog_info']
        data_info = db['data_info']

        while True:
            # latest catalog's date
            catalog_latest_document = catalog_info.find_one({'status': 'latest'})
            if catalog_latest_document:
                catalog_latest_date = str(catalog_latest_document['date'].date()).replace('-', '_')
            else:
                # TODO: error handling
                catalog_latest_date = None
                err = 'latest catalog does not exist'

            # user's latest riskreport date
            risk_report_latest_date = {}
            user_datas = list(data_info.find({'user_id': user_id}))
            for user_data in user_datas:
                risk_report_latest_date[user_data['name']] = user_data['riskreport']

                # TODO: if riskreport is outdated, show diff of records (& link to riskreport)
                if today_date > user_data['riskreport']:
                    err += '\n {} outdated'.format(user_data['name'])

            # determine file
            infos = list(data_info.find( {'user_id': user_id} ))

            if not infos:
                msg = 'まずは，genome fileをアップロードしましょう!'
                break

            break

    return direct_to_template(request,
                              'dashboard.html',
                              {'msg': msg, 'err': err,
                               'catalog_latest_date': catalog_latest_date,
                               'risk_report_latest_date': risk_report_latest_date})
