# -*- coding: utf-8 -*-

from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client
from django.conf import settings

from django.utils.translation import ugettext as _
from django.utils.translation import activate as translation_activate

import mongo.import_variants as import_variants
# from lib.utils.date import now_date

import sys
import os
import pymongo


class SimpleTest(TestCase):
    def setUp(self):
        # create test user
        self.client = Client()
        self.test_user_id = settings.TEST_USER_ID
        self.test_user_password = settings.TEST_USER_PASSWORD
        self.dummy_user_id = settings.TEST_DUMMY_USER_ID
        self.failUnlessEqual(bool(self.test_user_id != self.dummy_user_id), True)
        user = User.objects.create_user(self.test_user_id,
                                        '',
                                        self.test_user_password)
        self.test_user_dir = os.path.join(settings.RISKREPORT_CACHE_DIR, self.test_user_id)
        if not os.path.exists(self.test_user_dir):
            os.mkdir(self.test_user_dir)

        translation_activate('en')

        self.file_raw_path = settings.TEST_23ANDME_FILE
        self.file_raw_name = os.path.basename(settings.TEST_23ANDME_FILE)
        self.file_cleaned_name = self.file_raw_name.replace('.', '').replace(' ', '')


    def _delete_data(self):
        """Delete existing test-data.
        """

        with pymongo.Connection(port=settings.MONGO_PORT) as connection:
            db = connection['pergenie']
            data_info = db['data_info']

            # delete collection `variants.user_id.filename`
            db.drop_collection('variants.{0}.{1}'.format(self.test_user_id, self.file_cleaned_name))

            # because it is just a test, no need to delete `file`

            # delete document in `data_info`
            if data_info.find_one({'user_id': self.test_user_id}):
                data_info.remove({'user_id': self.test_user_id})


#     def upload_data(self):
#         """Import test-data.
#         """

#         with pymongo.Connection(port=settings.MONGO_PORT) as connection:
#             db = connection['pergenie']
#             data_info = db['data_info']

#             today =

#             # add data_info
#             info = {'user_id': self.test_user_id,
#                     'name': self.file_cleaned_name,
#                     'raw_name': self.file_raw_name,
#                     'date': today,
#                     'population': 'unknown',
#                     'sex': 'unknown',
#                     'file_format': 'andme',
#                     'status': float(0.0)}
#             data_info.insert(info)

#             # add variants.user_id.file_cleaned_name
#             import_error_state = import_variants.import_variants(self.file_raw_path,
#                                                                  'unknown',
#                                                                  'unknown',
#                                                                  'andme',
#                                                                  self.test_user_id)
#             print import_error_state

#         # TODO: mongo

    # def test_login_required(self):
    #     pass

    # TODO: check if is_invalid form


    def test_data_no_data_uploaded(self):
        self.client.login(username=self.test_user_id, password=self.test_user_password)

        self._delete_data()

        response = self.client.get('/riskreport/')
        self.failUnlessEqual(response.context['err'], 'no data uploaded')


    # TODO: status < 100 の状態をどうつくるか．
    # def test_is_importing(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)

    #     self.delete_data()
    #     self.upload_data()

    #     response = self.client.get('/riskreport/')

    #     err = _('%(file_name)s is in importing, please wait for seconds...') % {'file_name': self.file_cleaned_name}
    #     self.failUnlessEqual(response.context['err'], err)


    # def test_success(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)

    #     self.delete_data()
    #     self.upload_data()

    #     response = self.client.get('/riskreport/')

    #     self.failUnlessEqual(response.context['err'], '')






# def addition():
#     """
#     >>> 1+1
#     2
#     """
#     pass
