# -*- coding: utf-8 -*-

from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client
from django.conf import settings

from django.utils.translation import ugettext as _
from django.utils.translation import activate as translation_activate

from lib.mongo.import_variants import import_variants

import sys, os
import datetime
from pymongo import MongoClient


class SimpleTest(TestCase):
    def setUp(self):
        translation_activate('en')

        # create user
        self.client = Client()
        self.test_user_id = settings.TEST_USER_ID
        self.test_user_password = settings.TEST_USER_PASSWORD
        self.dummy_user_id = settings.TEST_DUMMY_USER_ID
        self.failUnlessEqual(bool(self.test_user_id != self.dummy_user_id), True)
        self.user = User.objects.create_user(self.test_user_id,
                                             '',
                                             self.test_user_password)

        # no need to make directory for upload, because we will import stored data.

        # create user_info
        with MongoClient(host=settings.MONGO_URI) as c:
            user_info = c['pergenie']['user_info']
            user_info.insert({'user_id': self.test_user_id,
                              'risk_report_show_level': 'show_all',
                              'activation_key': ''})

        self.file_raw_path = settings.TEST_23ANDME_FILE
        self.file_raw_name = os.path.basename(settings.TEST_23ANDME_FILE)
        self.file_cleaned_name = self.file_raw_name.replace('.', '').replace(' ', '')

    def _import_data(self):
        """Import genome data for test.
        """

        with MongoClient(host=settings.MONGO_URI) as c:
            catalog_cover_rate = c['pergenie']['catalog_cover_rate']
            info = {'user_id': self.test_user_id,
                    'name': self.file_cleaned_name,
                    'raw_name': self.file_raw_name,
                    'date': datetime.datetime.today(),
                    'population': 'unknown',
                    'file_format': 'andme',
                    'catalog_cover_rate': catalog_cover_rate.find_one({'stats': 'catalog_cover_rate'})['values']['andme'],
                    'genome_cover_rate': catalog_cover_rate.find_one({'stats': 'genome_cover_rate'})['values']['andme'],
                    'status': float(0.0)}

            data_info = c['pergenie']['data_info']
            data_info.insert(info)

            import_variants(file_path=self.file_raw_path,
                            population='unknown',
                            file_format='andme',
                            user_id=self.test_user_id)

    def _delete_data(self):
        """Delete existing *test data*.
        """

        with MongoClient(host=settings.MONGO_URI) as c:
            db = c['pergenie']
            data_info = db['data_info']

            # delete collection `variants.user_id.filename`
            db.drop_collection('variants.{0}.{1}'.format(self.test_user_id, self.file_cleaned_name))

            # because it is just a test, no need to delete `file`

            # delete document in `data_info`
            if data_info.find_one({'user_id': self.test_user_id}):
                data_info.remove({'user_id': self.test_user_id})

            user_info = c['pergenie']['user_info']
            user_info.update({'user_id': self.test_user_id,
                              'file_name': self.file_cleaned_name},
                             {'$set': {'last_viewed_file': ''}}, upsert=True)

    def test_login_required(self):
        response = self.client.get('/riskreport/')
        self.assertEqual(response.status_code, 302)

        # TODO: check all studies?
        response = self.client.get('/riskreport/もやもや病%28ウィリス動脈輪閉塞症%29/A%20genome-wide%20association%20study%20identifies%20RNF213%20as%20the%20first%20Moyamoya%20disease%20gene./')
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/riskreport/もやもや病%28ウィリス動脈輪閉塞症%29/A%20genome-wide%20association%20study%20identifies%20RNF213%20as%20the%20first%20Moyamoya%20disease%20gene./?file_name=' + self.file_cleaned_name)
        self.assertEqual(response.status_code, 302)

    def test_index_success(self):
        self.client.login(username=self.test_user_id, password=self.test_user_password)
        self._import_data()

        response = self.client.get('/riskreport/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['err'], '')
        self._delete_data()

    def test_index_no_data_uploaded(self):
        self.client.login(username=self.test_user_id, password=self.test_user_password)
        self._delete_data()

        response = self.client.get('/riskreport/')
        self.assertEqual(response.context['err'], 'no data uploaded')

    def test_index_file_is_in_importing(self):
        self.client.login(username=self.test_user_id, password=self.test_user_password)
        self._import_data()

        # create *in importing* file
        with MongoClient(host=settings.MONGO_URI) as c:
            data_info = c['pergenie']['data_info']
            data_info.update({'name': self.file_cleaned_name,
                              'user_id': self.test_user_id},
                             {"$set": {'status': float(50.0)}})

        response = self.client.post('/riskreport/', {'file_name': self.file_cleaned_name})
        self.assertEqual(response.context['err'], '{} is in importing, please wait for seconds...'.format(self.file_cleaned_name))
        self._delete_data()

    def test_index_files_are_in_importing(self):
        self.client.login(username=self.test_user_id, password=self.test_user_password)
        self._import_data()

        # create *in importing* file
        with MongoClient(host=settings.MONGO_URI) as c:
            data_info = c['pergenie']['data_info']
            data_info.update({'name': self.file_cleaned_name,
                              'user_id': self.test_user_id},
                             {"$set": {'status': float(50.0)}})

        response = self.client.get('/riskreport/')
        self.assertEqual(response.context['err'], 'Your files are in importing, please wait for seconds...')
        self._delete_data()

    def test_index_no_such_file(self):
        self.client.login(username=self.test_user_id, password=self.test_user_password)
        self._import_data()

        response = self.client.post('/riskreport/', {'file_name': 'dummytxt'})
        self.assertEqual(response.context['err'], 'no such file dummytxt')
        self._delete_data()

    # TODO: will get 302... ?
    # def test_study_success(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     response = self.client.get('/riskreport/もやもや病%28ウィリス動脈輪閉塞症%29/A%20genome-wide%20association%20study%20identifies%20RNF213%20as%20the%20first%20Moyamoya%20disease%20gene./')
    #     self.assertEqual(response.status_code, 200)
    #     self._delete_data()

    def test_study_nosuch_file(self):
        self.client.login(username=self.test_user_id, password=self.test_user_password)
        self._import_data()

        response = self.client.get('/riskreport/もやもや病%28ウィリス動脈輪閉塞症%29/A%20genome-wide%20association%20study%20identifies%20RNF213%20as%20the%20first%20Moyamoya%20disease%20gene./?file_name=' + 'dummy')
        self.assertEqual(response.status_code, 404)
        self._delete_data()
