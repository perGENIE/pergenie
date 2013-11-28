# -*- coding: utf-8 -*-

from pprint import pprint
from pymongo import MongoClient

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from django.conf import settings

from lib.mongo.import_variants import import_variants
from lib.test import LoginUserTestCase
from lib.utils.clogging import getColorLogger
log = getColorLogger(__name__)


class SimpleTestCase(LoginUserTestCase):
    def _setUp(self):
        self.app_name = __name__.split('.')[1]

    def test_login_required(self):
        self._test_login_required(self.app_name)



    # def test_menu_bar(self):
    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     response = self.client.get('/dashboard/')

        # test, user_id showed correctly
        # menu_bar_user_id = '''
        # <a href="#" class="dropdown-toggle" data-toggle="dropdown">
        # <i class="icon-unlock"></i>
        # {}
        # <b class="caret"></b>
        # </a>'''.format(self.dummy_user_id)
        # self.failUnlessEqual(bool(menu_bar_user_id in response.content), False)

#         menu_bar_user_id = '''<a href="#" class="dropdown-toggle" data-toggle="dropdown">
# <i class="icon-unlock"></i>
# {}
# <b class="caret"></b>
# </a>'''.format(self.test_user_id)
#         self.failUnlessEqual(bool(menu_bar_user_id in response.content), True)


        # TODO: check cookies & session data


    # def test_msg(self):
    #     """ """


    #         # print list(data_info.find())

    #     #TODO: test, msg for 'no file uploaded' shows correctly.
    #     #TODO: test, latest catalog...

    #     self.client.login(username=self.test_user_id, password=self.test_user_password)
    #     response = self.client.get('/dashboard/')
    #     # print 'response', response
    #     # print '.content', response.content
    #     # print '.context', response.context
    #     # print '.request', response.request
    #     # print '.status_code', response.status_code

    #     print response.context['msg']

    #     pass
