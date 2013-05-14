# from django.core import management

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from django.conf import settings

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
        # user does not exist
        self.failUnlessEqual(self.client.login(username=self.dummy_user_id, password='anonymousLogin'), False)

        # incorrect password
        self.failUnlessEqual(self.client.login(username=self.test_user_id, password='incorrectPassword'), False)

        # success
        self.failUnlessEqual(self.client.login(username=self.test_user_id, password=self.test_user_password), True)


    def test_register(self):
        # passwords do not match
        response = self.client.post('/register/', {'user_id': self.test_user_id,
                                                   'password1': 'pwd1',
                                                   'password2': 'pwd2'})
        self.failUnlessEqual(bool(response.context['message'] == 'Passwords do not match.'), True)

        # reserved_user_id
        response = self.client.post('/register/', {'user_id': self.test_user_id,
                                                   'password1': self.test_user_password,
                                                   'password2': self.test_user_password})
        self.failUnlessEqual(bool('Already registered.' in response.context['message']), True)

        # # success
        # response = self.client.post('/register/', {'user_id': 'user',
        #                                            'password1': 'pwd1',
        #                                            'password2': 'pwd1'}, follow=True)
        # self.failUnlessEqual(response.status_code, 200)
        # self.failUnlessEqual(bool('<title>Dashboard - perGENIE</title>' in response.content), True)

        # TODO: add other password check
        # TODO: with mail activation
