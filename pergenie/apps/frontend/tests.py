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

        # attempt to access /dashboard/ without login
        # -> redirect to /login/?next=/dashboard/
        response = self.client.get('/dashboard/')
        self.failUnlessEqual(response.status_code, 302)

        # attempt to access /dashboard/ after login
        self.client.login(username='temp', password='temp')
        response = self.client.get('/dashboard/')
        self.failUnlessEqual(response.status_code, 200)

