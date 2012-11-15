"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

# from django.core import management

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client


class SimpleTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        user = User.objects.create_user('temp', '', 'temp')
        # user.save()

        # options = dict(verbosity=0,)
        # management.call_command('loaddata', 'task/fixtures/test.json', **options)

    def test_get_index_page(self):
        """ """
        response = self.client.get('/', follow=True)
        self.failUnlessEqual(response.status_code, 200)

    def test_get_login_page(self):
        """ """
        response = self.client.get('/login/')
        self.failUnlessEqual(response.status_code, 200)

    def test_login(self):
        """ """
        self.failUnlessEqual(self.client.login(username='anonymous', password='anonymous'), False)
        self.failUnlessEqual(self.client.login(username='temp', password='temp'), True)

    def test_login_required(self):
        """ """
        response = self.client.get('/dashboard/')
        self.failUnlessEqual(response.status_code, 302)

        self.client.login(username='temp', password='temp')
        response = self.client.get('/dashboard/')
        self.failUnlessEqual(response.status_code, 200)

