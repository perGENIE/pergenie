# -*- coding: utf-8 -*-

from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client
from django.conf import settings

# import pymongo


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
        # TDOO: >>> csrf_client = Client(enforce_csrf_checks=True)

    def test_login_required(self):
        for page in ['/upload/', '/upload/status']:
            self.client.logout()
            # without login -> redirect to /login/?next=/upload/
            response = self.client.get(page)
            self.failUnlessEqual(response.status_code, 302)

            # user does not exist
            self.client.login(username=self.dummy_user_id, password='anonymousLogin')
            response = self.client.get(page)
            self.failUnlessEqual(response.status_code, 302)

            # incorrect password
            self.client.login(username=self.test_user_id, password='incorrectPassword')
            response = self.client.get(page)
            self.failUnlessEqual(response.status_code, 302)

            # success
            self.client.login(username=self.test_user_id, password=self.test_user_password)
            response = self.client.get(page)
            self.failUnlessEqual(response.status_code, 200)

    def test_celery_job_add(self):
        """Check if celery-job works
        """
        from lib.tasks import add
        from time import sleep

        r = add.delay(5, 5)
        sleep(1)

        self.failUnlessEqual(r.successful(), True)
        self.failUnlessEqual(r.result, 10)

    # def test_upload(self):
    #     response = self.client.get('/upload/')
    #     self.client.login(username='temp', password='temp')

    #     with open('data/genome_Greg_Mendel_Dad__Full_20121008014520.txt') as fp:
    #         response = self.client.post('/upload/', {'population': 'unknown',
    #                                                  'sex': 'unknown',
    #                                                  'file_format': 'andme',
    #                                                  'call': fp})
    #         print response.context['err']
    #         # assert something like 'population': 'aaa' -> err = 'populationを...'

    #         # TODO: need to test with MongoDB
    #         # いまのままだと，本番用のdbをみにいってる...

    #         # TODO: qimport動いてないっぽい?

    #     #
    #     self.failUnlessEqual(response.status_code, 200)
