# -*- coding: utf-8 -*-

import sys
import os
import time
import datetime

from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.translation import activate as translation_activate

from lib.test import LoginUserTestCase
from utils.clogging import getColorLogger
log = getColorLogger(__name__)


class SimpleTest(LoginUserTestCase):
    def test_login_required(self):
        response = self.client.get('/riskreport/')
        self.assertEqual(response.status_code, 302)

        # TODO: check all studies?
        response = self.client.get('/riskreport/もやもや病%28ウィリス動脈輪閉塞症%29/A%20genome-wide%20association%20study%20identifies%20RNF213%20as%20the%20first%20Moyamoya%20disease%20gene./')
        self.assertEqual(response.status_code, 302)

        response = self.client.get('/riskreport/もやもや病%28ウィリス動脈輪閉塞症%29/A%20genome-wide%20association%20study%20identifies%20RNF213%20as%20the%20first%20Moyamoya%20disease%20gene./?file_name=' + self.file_cleaned_name)
        self.assertEqual(response.status_code, 302)

    # def test_index_success(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     response = self.client.get('/riskreport/')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertEqual(response.context['err'], '')

    # def test_index_no_data_uploaded(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)

    #     response = self.client.get('/riskreport/')
    #     self.assertEqual(response.context['err'], 'no data uploaded')

    # def test_index_file_is_in_importing(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     # create *in importing* file
    #     with MongoClient(host=settings.MONGO_URI) as c:
    #         data_info = c['pergenie']['data_info']
    #         data_info.update({'name': self.file_cleaned_name,
    #                           'user_id': self.test_user_id},
    #                          {"$set": {'status': float(50.0)}})

    #     response = self.client.post('/riskreport/', {'file_name': self.file_cleaned_name})
    #     self.assertEqual(response.context['err'], '{0} is in importing, please wait for seconds...'.format(self.file_cleaned_name))

    # def test_index_files_are_in_importing(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     # create *in importing* file
    #     with MongoClient(host=settings.MONGO_URI) as c:
    #         data_info = c['pergenie']['data_info']
    #         data_info.update({'name': self.file_cleaned_name,
    #                           'user_id': self.test_user_id},
    #                          {"$set": {'status': float(50.0)}})
    #         data_info.update({'name': self.file_cleaned_name_2,
    #                           'user_id': self.test_user_id},
    #                          {"$set": {'status': float(50.0)}})

    #     response = self.client.get('/riskreport/')
    #     self.assertEqual(response.context['err'], 'Your files are in importing, please wait for seconds...')

    # def test_index_success_imported_file_and_importing_file(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     # create *in importing* file
    #     with MongoClient(host=settings.MONGO_URI) as c:
    #         data_info = c['pergenie']['data_info']
    #         data_info.update({'name': self.file_cleaned_name,
    #                           'user_id': self.test_user_id},
    #                          {"$set": {'status': float(50.0)}})

    #     # if there is *imported* file and *in importing* file,
    #     # show *imported* file.
    #     response = self.client.get('/riskreport/')
    #     self.assertTrue('<option value="testvcf40vcf" selected>' in response.content)

    # def test_index_no_such_file(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     response = self.client.post('/riskreport/', {'file_name': 'dummytxt'})
    #     self.assertEqual(response.context['err'], 'no such file dummytxt')


    # # TODO: will get 302... ?
    # # def test_study_success(self):
    # #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    # #     self._import_data()

    # #     response = self.client.get('/riskreport/もやもや病%28ウィリス動脈輪閉塞症%29/A%20genome-wide%20association%20study%20identifies%20RNF213%20as%20the%20first%20Moyamoya%20disease%20gene./')
    # #     self.assertEqual(response.status_code, 200)

    # def test_study_nosuch_file(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     response = self.client.get('/riskreport/もやもや病%28ウィリス動脈輪閉塞症%29/A%20genome-wide%20association%20study%20identifies%20RNF213%20as%20the%20first%20Moyamoya%20disease%20gene./?file_name=' + 'dummy')
    #     self.assertEqual(response.status_code, 404)

    # def test_index_not_change_population_or_file(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     response = self.client.get('/riskreport/')
    #     self.assertTrue('<option value="test23andmetxt" selected>' in response.content)
    #     self.assertTrue('<option value="unknown" selected>' in response.content)

    #     response = self.client.post('/riskreport/', {'file_name': self.file_cleaned_name,
    #                                                  'population': self.file_population})
    #     self.assertTrue('<option value="test23andmetxt" selected>' in response.content)
    #     self.assertTrue('<option value="unknown" selected>' in response.content)

    # def test_index_change_population(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     response = self.client.get('/riskreport/')
    #     self.assertTrue('<option value="test23andmetxt" selected>' in response.content)
    #     self.assertTrue('<option value="unknown" selected>' in response.content)

    #     response = self.client.post('/riskreport/', {'file_name': self.file_cleaned_name,
    #                                                  'population': 'Japanese'})
    #     self.assertTrue('<option value="test23andmetxt" selected>' in response.content)
    #     self.assertTrue('<option value="Japanese" selected>' in response.content)

    # def test_index_change_file(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     self._import_data()

    #     response = self.client.get('/riskreport/')
    #     self.assertTrue('<option value="test23andmetxt" selected>' in response.content)

    #     response = self.client.post('/riskreport/', {'file_name': self.file_cleaned_name_2,
    #                                                  'population': self.file_population})
    #     self.assertTrue('<option value="testvcf40vcf" selected>' in response.content)
    #     self.assertTrue('<option value="unknown" selected>' in response.content)
