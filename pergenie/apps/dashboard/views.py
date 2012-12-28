# -*- coding: utf-8 -*- 

from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from django.conf import settings

import os
import pymongo

from utils.io import pickle_load_obj
from utils.date import today_date

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
            # latest catalog importing date
            catalog_latest_importing_document = catalog_info.find_one({'status': 'latest'})
            if catalog_latest_importing_document:
                catalog_latest_importing_date = str(catalog_latest_importing_document['date'].date()).replace('-', '_')
            else:
                # TODO: error handling
                catalog_latest_importing_date = None
                err = 'latest catalog does not exist'

            # latest new catalog records date
            catalog_summary = pickle_load_obj(os.path.join(settings.CATALOG_SUMMARY_CACHE_DIR, 'catalog_summary.p'))
            catalog_latest_new_records_data = sorted(catalog_summary.get('added').items())[-1]

            # user's latest riskreport date
            risk_report_latest_date = {}
            user_datas = list(data_info.find({'user_id': user_id}))
            for user_data in user_datas:
                risk_report_latest_date[user_data['name']] = user_data['riskreport']

                # if riskreport is outdated, show diff of records (& link to riskreport)
                if today_date > user_data['riskreport']:
                    err += '\n {} outdated'.format(user_data['name'])
                    err += '\n last risk report: {}'.format(user_data['riskreport'])
                    
                for added_date in sorted(catalog_summary.get('added').items()):
                    print added_date[0],  catalog_latest_importing_document['date']
                    if added_date[0] > catalog_latest_importing_document['date']:
                        err += '\n {1} new records {0}'.format(added_date[0], added_date[1])

            # determine file
            infos = list(data_info.find( {'user_id': user_id} ))

            if not infos:
                msg = 'まずは，genome fileをアップロードしましょう!'
                break

            break

    return direct_to_template(request,
                              'dashboard.html',
                              {'msg': msg, 'err': err,
                               'catalog_latest_importing_date': catalog_latest_importing_date,
                               'catalog_latest_new_records_data': catalog_latest_new_records_data,
                               'risk_report_latest_date': risk_report_latest_date})
