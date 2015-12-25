from django.test import TestCase
from splinter import Browser

from .models import UserActivation, User


class AuthenticationLoginBrowserTestCase(TestCase):
    def setUp(self):
        self.browser = Browser('django')
        self.test_user_id = 'test-user@pergenie.org'
        self.test_user_password = 'test-user-password'
        self.user = User.objects.create_user(username=self.test_user_id,
                                             email=self.test_user_id,
                                             password=self.test_user_password)
        self.user.save()

        assert len(User.objects.all()) == 1
        assert User.objects.first().is_active is False

        self.browser.visit('/login')

    def test_login_page_ok(self):
        assert '/login' in self.browser.url

    def test_login_ok(self):
        self.user.is_active = True
        self.user.save()

        self.browser.fill('email', self.test_user_id)
        self.browser.fill('password', self.test_user_password)
        self.browser.find_by_name('submit').click()
        assert '/dashboard' in self.browser.url

    def test_logout_ok(self):
        self.user.is_active = True
        self.user.save()

        # login
        self.browser.fill('email', self.test_user_id)
        self.browser.fill('password', self.test_user_password)
        self.browser.find_by_name('submit').click()

        # logout
        self.browser.visit('/logout')
        assert 'login' in self.browser.title.lower()

    def test_too_long_email_should_fail_login(self):
        self.browser.fill('email', 'a' * 254 + '@pergenie.org')
        self.browser.fill('password', self.test_user_password)
        self.browser.find_by_name('submit').click()
        assert self.browser.is_text_present('invalid mail address or password')

    def test_not_exist_user_should_fail_login(self):
        self.browser.fill('email', 'not-exist-user@pergenie.org')
        self.browser.fill('password', 'not-exist-user-password')
        self.browser.find_by_name('submit').click()
        assert self.browser.is_text_present('invalid mail address or password')

    def test_incorrect_password_should_fail_login(self):
        self.browser.fill('email', self.test_user_id)
        self.browser.fill('password', 'incorrect-password')
        self.browser.find_by_name('submit').click()
        assert self.browser.is_text_present('invalid mail address or password')

    def test_not_active_user_should_fail_login(self):
        self.browser.fill('email', self.test_user_id)
        self.browser.fill('password', self.test_user_password)
        self.browser.find_by_name('submit').click()
        assert self.browser.is_text_present('invalid mail address or password')


class AuthenticationRegisterBrowserTestCase(TestCase):
    def setUp(self):
        self.browser = Browser('django')
        self.test_user_id = 'test-user@pergenie.org'
        self.test_user_password = 'test-user-password'

    def test_register_page_ok(self):
        self.browser.visit('/register')
        assert '/register' in self.browser.url

    def test_register_ok(self):
        self.browser.visit('/register')
        self.browser.fill_form({'email': self.test_user_id,
                                'password1': self.test_user_password,
                                'password2': self.test_user_password,
                                'terms_ok_0': True,
                                'terms_ok_1': True})
        self.browser.find_by_name('submit').click()
        assert 'registeration completed' in self.browser.title.lower()

        user = User.objects.get(email=self.test_user_id)
        assert user.is_active is False

    def test_activation_ok(self):
        self.browser.visit('/register')
        self.browser.fill_form({'email': self.test_user_id,
                                'password1': self.test_user_password,
                                'password2': self.test_user_password,
                                'terms_ok_0': True,
                                'terms_ok_1': True})
        self.browser.find_by_name('submit').click()

        user = User.objects.get(email=self.test_user_id)
        activation_key = UserActivation.objects.get(user=user).activation_key
        assert user.is_active is False
        assert UserActivation.objects.filter(activation_key=activation_key).exists() is True

        self.browser.visit('/activation/' + activation_key)
        assert 'activation completed' in self.browser.title.lower()

        user = User.objects.get(email=self.test_user_id)
        assert user.is_active is True
        assert UserActivation.objects.filter(activation_key=activation_key).exists() is False

    def test_too_long_email_should_fail_register(self):
        self.browser.visit('/register')
        self.browser.fill_form({'email': 'a' * 254 + '@pergenie.org',
                                'password1': self.test_user_password,
                                'password2': self.test_user_password,
                                'terms_ok_0': True,
                                'terms_ok_1': True})
        self.browser.find_by_name('submit').click()
        assert self.browser.is_text_present('Ensure this value has at most 254')

    def test_too_long_password_should_fail_register(self):
        self.browser.visit('/register')
        self.browser.fill_form({'email': self.test_user_id,
                                'password1': 'a' * 1025,
                                'password2': 'a' * 1025,
                                'terms_ok_0': True,
                                'terms_ok_1': True})
        self.browser.find_by_name('submit').click()
        assert self.browser.is_text_present('Ensure this value has at most 1024')

    def test_too_weak_password_should_fail_register(self):
        self.browser.visit('/register')
        self.browser.fill_form({'email': self.test_user_id,
                                'password1': 'weak',
                                'password2': 'weak',
                                'terms_ok_0': True,
                                'terms_ok_1': True})
        self.browser.find_by_name('submit').click()
        assert self.browser.is_text_present('Passwords too short')

    def test_not_match_passwords_should_fail_register(self):
        self.browser.visit('/register')
        self.browser.fill_form({'email': self.test_user_id,
                                'password1': self.test_user_password,
                                'password2': 'not-match-password',
                                'terms_ok_0': True,
                                'terms_ok_1': True})
        self.browser.find_by_name('submit').click()
        assert self.browser.is_text_present('Passwords do not match')

    def test_not_agree_with_terms_should_fail_register(self):
        self.browser.visit('/register')
        self.browser.fill_form({'email': self.test_user_id,
                                'password1': self.test_user_password,
                                'password2': self.test_user_password,
                                'terms_ok_0': False,
                                'terms_ok_1': True})
        self.browser.find_by_name('submit').click()
        assert self.browser.is_text_present('Not read and accept about service')

    def test_already_registerd_user_should_fail_register(self):
        self.user = User.objects.create_user(self.test_user_id,
                                             self.test_user_password)
        self.user.save()

        self.browser.visit('/register')
        self.browser.fill_form({'email': self.test_user_id,
                                'password1': self.test_user_password,
                                'password2': self.test_user_password,
                                'terms_ok_0': True,
                                'terms_ok_1': True})
        self.browser.find_by_name('submit').click()
        assert self.browser.is_text_present('Already registered')

    # TODO:
    def test_email_sending_error_should_fail_register(self):
        pass

    def test_incorrect_activation_key_should_fail_activation(self):
        self.browser.visit('/activation/' + 'a' * 40)
        assert self.browser.status_code == 404
