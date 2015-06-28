from django.conf import settings

from pymongo import MongoClient


mongo_con = MongoClient(host=settings.MONGO_URI)
mongo_db = mongo_con[settings.MONGO_DB_NAME]
