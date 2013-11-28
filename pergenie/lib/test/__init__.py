# -*- coding: utf-8 -*-

import sys, os
import time
import datetime
from pymongo import MongoClient

from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.translation import activate as translation_activate
from lib.utils.clogging import getColorLogger
log = getColorLogger(__name__)


class LoginUserTestCase(TestCase):
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
        self.file_raw_name = os.path.basename(self.file_raw_path)
        self.file_cleaned_name = self.file_raw_name.replace('.', '').replace(' ', '')
        self.file_population = 'unknown'

        self.file_raw_path_2 = settings.TEST_VCF40_FILE
        self.file_raw_name_2 = os.path.basename(self.file_raw_path_2)
        self.file_cleaned_name_2 = self.file_raw_name_2.replace('.', '').replace(' ', '')
        self.file_population_2 = 'unknown'

        # Call setUp for sub-class
        self._setUp()

    def tearDown(self):
        self._delete_data()

        # Call tearDown for sub-class
        self._tearDown()

    def _setUp(self):
        """Write test specific setUp in sub-class"""
        pass

    def _tearDown(self):
        """Write test specific tearDown in sub-class"""
        pass

    def _delete_data(self):
        """Delete test data
        """

        with MongoClient(host=settings.MONGO_URI) as c:
            db = c['pergenie']
            data_info = db['data_info']

            # delete collection `variants.user_id.filename`
            db.drop_collection('variants.{0}.{1}'.format(self.test_user_id, self.file_cleaned_name))
            db.drop_collection('variants.{0}.{1}'.format(self.test_user_id, self.file_cleaned_name_2))

            # because it is just a test, no need to delete `file`

            # delete document in `data_info`
            founds = list(data_info.find({'user_id': self.test_user_id}))
            if founds:
                for found in founds:
                    data_info.remove(found)

            user_info = c['pergenie']['user_info']
            user_info.update({'user_id': self.test_user_id},
                             {'$set': {'last_viewed_file': ''}}, upsert=True)

    def _test_login_required(self, app_name):
        # attempt to access /app_name/ without login
        # -> redirect to /login/?next=/app_name/
        response = self.client.get('/{app_name}/'.format(app_name=app_name))
        self.failUnlessEqual(response.status_code, 302)

        # attempt to access /app_name/ with login
        # but, user does not exist
        self.client.login(username=self.dummy_user_id, password='anonymousLogin')
        response = self.client.get('/{app_name}/'.format(app_name=app_name))
        self.failUnlessEqual(response.status_code, 302)

        # but, incorrect password
        self.client.login(username=self.test_user_id, password='incorrectPassword')
        response = self.client.get('/{app_name}/'.format(app_name=app_name))
        self.failUnlessEqual(response.status_code, 302)

        # success
        self.client.login(username=self.test_user_id, password=self.test_user_password)
        response = self.client.get('/{app_name}/'.format(app_name=app_name))
        self.failUnlessEqual(response.status_code, 200)

    def _test_logout(self, app_name):
        self.client.login(username=self.test_user_id, password=self.test_user_password)
        response = self.client.get('/{app_name}/'.format(app_name=app_name))
        response = self.client.get('/logout/')# , follow=True)
        self.failUnlessEqual(response.status_code, 302)
