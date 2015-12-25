# -*- coding: utf-8 -*-

from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client
from django.conf import settings
from django.utils.translation import ugettext as _
from django.utils.translation import activate as translation_activate

import os
import pymongo


class SimpleTest(TestCase):
    def setUp(self):
        # create test user
        self.client = Client()
        self.test_user_id = settings.TEST_USER_ID
        self.test_user_password = settings.TEST_USER_PASSWORD
        user = User.objects.create_user(self.test_user_id,
                                        '',
                                        self.test_user_password)

        translation_activate('en')

        # self.file_raw_path = settings.TEST_23ANDME_FILE
        # self.file_raw_name = os.path.basename(settings.TEST_23ANDME_FILE)
        # self.file_cleaned_name = self.file_raw_name.replace('.', '').replace(' ', '')

    def test_pass(self):
        pass

    # def test_data_no_data_uploaded(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)

    #     self.delete_data()
    #     response = self.client.get('/traits/')
    #     self.failUnlessEqual(response.context['err'], 'no data uploaded')
