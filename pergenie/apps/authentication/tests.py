from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from django.conf import settings
from django.utils.translation import ugettext as _


class SimpleTestCase(TestCase):
    def setUp(self):
        # create test user
        self.client = Client()
        self.test_user_id = settings.TEST_USER_ID
        self.test_user_password = settings.TEST_USER_PASSWORD
        self.dummy_user_id = settings.TEST_DUMMY_USER_ID
        self.assertNotEqual(self.test_user_id, self.dummy_user_id)
        self.user = User.objects.create_user(self.test_user_id,
                                             '',
                                             self.test_user_password)
        self.user.is_active = False
        self.user.save()

    def test_get_index_page(self):
        response = self.client.get('/', follow=True)
        self.assertEqual(response.status_code, 200)

    def test_get_login_page(self):
        response = self.client.get('/login/')
        self.assertEqual(response.status_code, 200)

    def test_login(self):
        # not activated
        self.assertFalse(self.user.is_active)
        response = self.client.post('/login/', {'user_id': self.test_user_id,
                                                'password': self.test_user_password})
        self.assertTrue(bool(response.context['err'] == 'invalid mail address or password'))

        # activate user
        self.user.is_active = True
        self.user.save()
        self.assertTrue(self.user.is_active)

        # user does not exist
        response = self.client.post('/login/', {'user_id': self.dummy_user_id,
                                                'password': self.test_user_password})
        self.assertTrue(bool(response.context['err'] == 'invalid mail address or password'))

        # incorrect password
        response = self.client.post('/login/', {'user_id': self.test_user_id,
                                                'password': self.test_user_password + '1'})
        self.assertTrue(bool(response.context['err'] == 'invalid mail address or password'))

        # success
        response = self.client.post('/login/', {'user_id': self.test_user_id,
                                                'password': self.test_user_password},
                                    follow=True)
        self.assertEqual(response.__dict__['request']['PATH_INFO'], '/dashboard/')

    def test_logout(self):
        self.user.is_active = True
        self.user.save()

        # login
        self.client.login(username=self.test_user_id, password=self.test_user_password)

        # logout
        response = self.client.post('/logout/', follow=True)
        self.assertEqual(response.__dict__['request']['PATH_INFO'], '/login/')

    def test_register(self):
        # password and confirm-password do not match
        response = self.client.post('/register/', {'user_id': self.test_user_id,
                                                   'password1': 'password123',
                                                   'password2': 'password1234'})
        self.assertEqual(response.context['err'], 'Passwords do not match.')

        # too short password
        response = self.client.post('/register/', {'user_id': self.test_user_id,
                                                   'password1': '123',
                                                   'password2': '123'})
        self.assertTrue(_('Passwords too short (passwords should be longer than %(min_password_length)s characters).' % {'min_password_length': settings.MIN_PASSWORD_LENGTH}) in response.context['err'])

        # invalid email address
        response = self.client.post('/register/', {'user_id': 'test_user_fail',
                                                   'password1': self.test_user_password,
                                                   'password2': self.test_user_password})
        self.assertEqual(response.context['err'], 'Invalid mail address assumed.')

        # invalid email address
        for x in settings.INVALID_USER_ID_CHARACTERS:
            response = self.client.post('/register/', {'user_id': x + self.test_user_id,
                                                       'password1': self.test_user_password,
                                                       'password2': self.test_user_password})
            self.assertEqual(response.context['err'], 'Invalid mail address assumed.')

        # RESERVED_USER_ID
        response = self.client.post('/register/', {'user_id': self.test_user_id,
                                                   'password1': self.test_user_password,
                                                   'password2': self.test_user_password})
        self.assertTrue('Already registered.' in response.context['err'])

        # # success
        # response = self.client.post('/register/', {'user_id': 'test_user_success@pergenie.org',
        #                                            'password1': self.test_user_password,
        #                                            'password2': self.test_user_password}, follow=True)
        # self.assertTrue('<title>Registeration completed - perGENIE</title>' in response.content)
