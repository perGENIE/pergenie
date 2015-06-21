from . import MongoTestCase


class TestMongoTestCase(MongoTestCase):
    def test_mongo_dummy_db_ok(self):
        dummy_collection = self.mongo_dummy_db['dummy']
        dummy_collection.insert_one({'ping': 'pong'})
        assert dummy_collection.find_one()['ping'] == 'pong'
