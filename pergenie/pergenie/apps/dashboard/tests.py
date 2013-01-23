# -*- coding: utf-8 -*- 

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from django.conf import settings

from pprint import pprint 
import pymongo


class SimpleTestCase(TestCase):
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

        # #
        # with pymongo.Connection(port=settings.MONGO_PORT) as connection:
        #     db = connection['pergenie']
        #     catalog_info = db['catalog_info']
        #     data_info = db['data_info']

        #     # init test user
        #     test_user_data_info = data_info.find_one({'user_id': self.test_user_id})
        #     self.failUnlessEqual(bool(test_user_data_info == None), True)
            


    def test_login_required(self):
        # attempt to access /dashboard/ without login
        # -> redirect to /login/?next=/dashboard/
        response = self.client.get('/dashboard/')
        self.failUnlessEqual(response.status_code, 302)

        # attempt to access /dashboard/ with login
        # but, user does not exist
        self.client.login(username=self.dummy_user_id, password='anonymousLogin')
        response = self.client.get('/dashboard/')
        self.failUnlessEqual(response.status_code, 302)

        # but, incorrect password
        self.client.login(username=self.test_user_id, password='incorrectPassword')
        response = self.client.get('/dashboard/')
        self.failUnlessEqual(response.status_code, 302)

        # success
        self.client.login(username=self.test_user_id, password=self.test_user_password)
        response = self.client.get('/dashboard/')
        self.failUnlessEqual(response.status_code, 200)


    def test_menu_bar(self):
        self.client.login(username=self.test_user_id, password=self.test_user_password)
        response = self.client.get('/dashboard/')

        # test, user_id showed correctly
        menu_bar_user_id = 'Logged in as <a href="/settings/">{}</a>'.format(self.dummy_user_id)
        self.failUnlessEqual(bool(menu_bar_user_id in response.content), False)

        menu_bar_user_id = 'Logged in as <a href="/settings/">{}</a>'.format(self.test_user_id)
        self.failUnlessEqual(bool(menu_bar_user_id in response.content), True)


    def test_logout(self):
        self.client.login(username=self.test_user_id, password=self.test_user_password)
        response = self.client.get('/dashboard/')
        response = self.client.get('/logout/')# , follow=True)
        self.failUnlessEqual(response.status_code, 302)
        
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
