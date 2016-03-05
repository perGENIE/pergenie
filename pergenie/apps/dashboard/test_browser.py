from django.test import TestCase
from splinter import Browser
import pytest

from test.utils import auth


class DashboardTestCase(TestCase):
    def setUp(self):
        self.test_user_id = 'test-user@pergenie.org'
        self.test_user_password = 'test-user-password'
        self.user = auth.create_user(self.test_user_id, self.test_user_password, is_active=True)

        self.browser = auth.browser_login(Browser('django'), self.test_user_id, self.test_user_password)
        self.browser.visit('/dashboard')

    def test_login_required(self):
        assert 'dashboard' in self.browser.title.lower()

    def test_menu_bar_contains_user_id(self):
        assert self.browser.find_by_id('menu_user_id')[0].text.replace(' ', '').strip() == self.test_user_id

    def test_menu_bar_contains_apps(self):
        assert [x.strip() for x in self.browser.find_by_id('menu_apps')[0].text.split(' ') if x.strip() != ''] == ['Dashboard', 'RiskReport', 'Genomes']

    def test_dashboard_menu_contains_apps(self):
        assert [x.strip() for x in self.browser.find_by_id('dashboard_menu')[0].text.split(' ') if x.strip() != ''] == ['RiskReport', 'Genomes']
