# -*- coding: utf-8 -*-

# from pymongo import MongoClient
# from django.conf import settings
from lib.test import LoginUserTestCase
from lib.utils.clogging import getColorLogger
log = getColorLogger(__name__)


class SimpleTestCase(LoginUserTestCase):
    def _setUp(self):
        self.app_name = __name__.split('.')[1]

    def test_login_required(self):
        log.info('test_login_required')
        self._test_login_required('/upload/')
        self._test_login_required('/upload/status')

    def test_celery_job_add(self):
        """Check if celery-job works

        * if fails with `error: [Errno 61] Connection refused]`, rabbitmq-server may not be working
        * if fails with `AssertionError: False != True`, celery may not be working

        """
        from lib.tasks import add
        from time import sleep

        r = add.delay(5, 5)
        sleep(1)

        self.failUnlessEqual(r.successful(), True)
        self.failUnlessEqual(r.result, 10)

    # TODO: write tests for /upload

    def test_upload_success(self):
        pass

    def test_upload_invalid_request(self):
        pass



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
