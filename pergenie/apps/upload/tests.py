# -*- coding: utf-8 -*- 

"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.test.client import Client

import pymongo

class SimpleTest(TestCase):
    def setUp(self):
        self.client = Client()
        user = User.objects.create_user('temp', '', 'temp')
        
        # # TODO: Load db for test
        # connection = pymongo.Connection()


    def test_upload_valid(self):
        response = self.client.get('/upload/')
        self.client.login(username='temp', password='temp')

        with open('data/genome_Greg_Mendel_Dad__Full_20121008014520.txt') as fp:
            response = self.client.post('/upload/', {'population': 'unknown',
                                                     'sex': 'unknown',
                                                     'file_format': 'andme',
                                                     'call': fp})
            print response.context['err']
            # assert something like 'population': 'aaa' -> err = 'populationを...'

            # TODO: need to test with MongoDB
            # いまのままだと，本番用のdbをみにいってる...

            # TODO: qimport動いてないっぽい?
            
            

        #
        self.failUnlessEqual(response.status_code, 200)
