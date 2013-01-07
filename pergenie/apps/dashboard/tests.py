from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

class SimpleTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        user = User.objects.create_user('temp', '', 'temp')

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
