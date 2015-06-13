from django.test import TestCase
from django.conf import settings
from django.utils.translation import ugettext as _

from splinter import Browser


class LandingBrowserTestCase(TestCase):
    def setUp(self):
        self.browser = Browser('django')

    def test_landing_page_ok(self):
        self.browser.visit('/')
        assert '/' in self.browser.url
        assert 'perGENIE' in self.browser.title

    def test_about_page_ok(self):
        self.browser.visit('/about')
        assert '/about' in self.browser.url
        assert 'about' in self.browser.title.lower()
