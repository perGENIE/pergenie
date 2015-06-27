from django.test import TestCase

from pergenie.mongo import mongo_db


class PingMongoTestCase(TestCase):
    def test_ping_mongo_ok(self):
        dummy_collection = mongo_db['dummy']
        dummy_collection.insert_one({'ping': 'pong'})

        assert dummy_collection.find_one()['ping'] == 'pong'

        mongo_db.drop_collection(dummy_collection)
