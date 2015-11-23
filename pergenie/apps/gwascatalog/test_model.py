from django.test import TestCase
from django.conf import settings
from django.utils.translation import ugettext as _

from .models import GWASCatalog


class GWASCatalogModelTestCase(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_gwascatalog_create_ok(self):
        pass

    def test_gwascatalog_delete_ok(self):
        pass

    def test_gwascatalog_get_latest_ok(self):
        catalog = GWASCatalog.objects.latest('created_at')
        pass
