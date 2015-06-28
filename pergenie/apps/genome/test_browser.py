import os
import json

from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings

from splinter import Browser

from pergenie.mongo import mongo_db
from test.utils import auth
from .models import Genome


@override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   CELERY_ALWAYS_EAGER=True,
                   BROKER_BACKEND='memory')
class GenomeBrowserTestCase(TestCase):
    def setUp(self):
        self.test_user_id = 'test-user@pergenie.org'
        self.test_user_password = 'test-user-password'
        self.user = auth.create_user(self.test_user_id, self.test_user_password, is_active=True)
        self.genome = None

        self.browser = auth.browser_login(Browser('django'), self.test_user_id, self.test_user_password)

    def tearDown(self):
        if self.genome:
            self.genome.delete_genotypes()
            self.genome.delete()

    def test_genome_index_page_login_required(self):
        self.browser.visit('/logout')
        self.browser.visit('/genome/upload')
        assert '/login' in self.browser.url

    def test_genome_index_page_ok(self):
        self.browser.visit('/genome/upload')
        assert 'upload' in self.browser.title.lower()

    def test_genome_upload_ok(self):
        # TODO: DRY
        self.browser.visit('/genome/upload')
        self.browser.attach_file('upload_files', os.path.join(settings.TEST_DATA_DIR, 'test_vcf42.vcf'))
        self.browser.select('file_format', Genome.FILE_FORMAT_VCF)
        self.browser.select('population', Genome.POPULATION_UNKNOWN)
        self.browser.select('sex', Genome.SEX_UNKNOWN)
        self.browser.find_by_name('submit').click()

        self.genome = Genome.objects.get(owner=self.user)

        assert self.genome.file_name == 'test_vcf42.vcf'
        assert self.genome.file_format == Genome.FILE_FORMAT_VCF
        assert self.genome.population == Genome.POPULATION_UNKNOWN
        assert self.genome.sex == Genome.SEX_UNKNOWN
        assert [x.id for x in self.genome.readers.all()] == [self.user.id]

        genotypes = self.genome.get_genotypes()

        assert genotypes.count() == 1

    def test_invalid_genome_file_should_fail_upload(self):
        pass

    def test_genome_delete_ok(self):
        # TODO: DRY
        self.browser.visit('/genome/upload')
        self.browser.attach_file('upload_files', os.path.join(settings.TEST_DATA_DIR, 'test_vcf42.vcf'))
        self.browser.select('file_format', Genome.FILE_FORMAT_VCF)
        self.browser.select('population', Genome.POPULATION_UNKNOWN)
        self.browser.select('sex', Genome.SEX_UNKNOWN)
        self.browser.find_by_name('submit').click()

        self.genome = Genome.objects.get(owner=self.user)

        self.browser.find_by_id('delete-yes-' + str(self.genome.id)).first.click()


    def test_not_exist_genome_should_fail_delete(self):
        # TODO:
        pass

    def test_genome_status_ok(self):
        # TODO: DRY
        self.browser.visit('/genome/upload')
        self.browser.attach_file('upload_files', os.path.join(settings.TEST_DATA_DIR, 'test_vcf42.vcf'))
        self.browser.select('file_format', Genome.FILE_FORMAT_VCF)
        self.browser.select('population', Genome.POPULATION_UNKNOWN)
        self.browser.select('sex', Genome.SEX_UNKNOWN)
        self.browser.find_by_name('submit').click()

        self.genome = Genome.objects.get(owner=self.user)

        self.browser.visit('/genome/status')
        response = json.loads(self.browser.html)
        expected = {'status': 'ok',
                    'error_message': '',
                    'uploaded_files': {str(self.genome.id): 100}}

        assert response == expected

    def test_genome_status_error(self):
        # TODO:
        pass
