# -*- coding: utf-8 -*- 

from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client
from django.conf import settings

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

        # TODO: mongo

    # def test_login_required(self):
    #     pass

    def test_data_not_uploaded(self):
        self.client.login(username=self.test_user_id, password=self.test_user_password)
        response = self.client.get('/riskreport/')

        # TODO: en/ja
        self.failUnlessEqual(bool(response.context['err'] == 'データがアップロードされていません．'), True)
        
        


# def addition():
#     """
#     >>> 1+1
#     2
#     """
#     pass
