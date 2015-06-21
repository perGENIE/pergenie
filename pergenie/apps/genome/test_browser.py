import os

from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings

from splinter import Browser

from test import MongoTestCase
from test.utils import auth
from .models import Genome


@override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   CELERY_ALWAYS_EAGER=True,
                   BROKER_BACKEND='memory')
class GenomeBrowserTestCase(MongoTestCase):
    def setUp(self):
        self.test_user_id = 'test-user@pergenie.org'
        self.test_user_password = 'test-user-password'
        self.user = auth.create_user(self.test_user_id, self.test_user_password, is_active=True)
        self.browser = auth.browser_login(Browser('django'), self.test_user_id, self.test_user_password)

    def test_genome_index_page_login_required(self):
        self.browser.visit('/logout')
        self.browser.visit('/genome/upload')
        assert '/login' in self.browser.url

    def test_genome_index_page_ok(self):
        self.browser.visit('/genome/upload')
        assert 'upload' in self.browser.title.lower()

    def test_genome_upload_ok(self):
        self.browser.visit('/genome/upload')
        self.browser.attach_file('upload_files', os.path.join(settings.TEST_DATA_DIR, 'test_genome_file.txt'))
        self.browser.select('file_format', Genome.FILE_FORMAT_VCF)
        self.browser.select('population', Genome.POPULATION_UNKNOWN)
        self.browser.select('sex', Genome.SEX_UNKNOWN)
        self.browser.find_by_name('submit').click()

    def test_invalid_genome_file_should_fail_upload(self):
        pass

    def test_genome_delete_ok(self):
        self.browser.visit('/genome/upload')
        self.browser.attach_file('upload_files', os.path.join(settings.TEST_DATA_DIR, 'test_genome_file.txt'))
        self.browser.select('file_format', Genome.FILE_FORMAT_VCF)
        self.browser.select('population', Genome.POPULATION_UNKNOWN)
        self.browser.select('sex', Genome.SEX_UNKNOWN)
        self.browser.find_by_name('submit').click()

        # click delete button of this genome file

    def test_not_exist_genome_should_fail_delete(self):
        pass

    def test_genome_status_ok(self):
        # create genome db record
        # - owner is login user
        # - owner is another user

        # check if geonme status contains only login user's genome

        self.browser.visit('/genome/status')
