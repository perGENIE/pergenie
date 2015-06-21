from django.test import TestCase
from django.conf import settings
from django.test.utils import override_settings

from pymongo import MongoClient


@override_settings(MONGO_DB_NAME=settings.MONGO_DB_NAME+'_dummy')
class MongoTestCase(TestCase):
    def _pre_setup(self):
        self.mongo_client = MongoClient(host=settings.MONGO_URI)
        self.mongo_dummy_db = self.mongo_client[settings.MONGO_DB_NAME]
        super(MongoTestCase, self)._pre_setup()

    def _post_teardown(self):
        self.mongo_client.drop_database(settings.MONGO_DB_NAME)
        super(MongoTestCase, self)._post_teardown()
