# -*- coding: utf-8 -*-

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from django.conf import settings


class SimpleTest(TestCase):
    def setUp(self):
        # create test user
        self.client = Client()
        self.test_user_id = settings.TEST_USER_ID
        self.test_user_password = settings.TEST_USER_PASSWORD
        User.objects.create_user(self.test_user_id,
                                 '',
                                 self.test_user_password)

    def test_success(self):
        self.client.login(username=self.test_user_id, password=self.test_user_password)
        response = self.client.get('/faq/')
        self.failUnlessEqual(response.status_code, 200)
