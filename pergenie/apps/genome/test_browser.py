import os
import json

from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings

from splinter import Browser

from test.utils import auth
from apps.gwascatalog.models import GwasCatalogSnp, GwasCatalogPhenotype
from .models import Genome
from lib.utils.population import POPULATION_UNKNOWN
from lib.utils.date import today_with_tz


@override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   CELERY_ALWAYS_EAGER=True,
                   BROKER_BACKEND='memory')
class GenomeBrowserTestCase(TestCase):
    def setUp(self):
        self.test_user_id = 'test-user@pergenie.org'
        self.test_user_password = 'test-user-password'
        self.user = auth.create_user(self.test_user_id, self.test_user_password, is_active=True)
        self.genomes = []

        self.browser = auth.browser_login(Browser('django'), self.test_user_id, self.test_user_password)

        # SNPs for whitelist
        phenotype, _ = GwasCatalogPhenotype.objects.get_or_create(name='test phenotype 1')
        GwasCatalogSnp(date_downloaded=today_with_tz,
                       pubmed_id='12345678',
                       phenotype=phenotype,
                       snp_id_current=527236043,  # rsLow rs6054257 => rsHigh rs527236043
                       population=['EastAsian']).save()

    def tearDown(self):
        if self.genomes:
            for genome in self.genomes:
                genome.delete_genotypes()
                genome.delete()

    def test_genome_index_page_login_required(self):
        self.browser.visit('/logout')
        self.browser.visit('/genome/upload')
        assert '/login' in self.browser.url

    def test_genome_index_page_ok(self):
        self.browser.visit('/genome/upload')
        assert 'upload' in self.browser.title.lower()

    def test_one_genome_upload_ok(self):
        self.browser.visit('/genome/upload')
        default = {'file_format': Genome.FILE_FORMAT_VCF,
                   'population': POPULATION_UNKNOWN,
                   'sex': Genome.SEX_UNKNOWN}
        self.browser.attach_file('upload_files', os.path.join(settings.TEST_DATA_DIR, 'test_vcf42.vcf'))
        self.browser.fill_form(default)
        self.browser.find_by_name('submit').click()

        self.genomes = [Genome.objects.get(owner=self.user)]

        assert self.genomes[0].file_name == 'test_vcf42.vcf'
        assert self.genomes[0].file_format == Genome.FILE_FORMAT_VCF
        assert self.genomes[0].population == POPULATION_UNKNOWN
        assert self.genomes[0].sex == Genome.SEX_UNKNOWN
        assert [x.id for x in self.genomes[0].readers.all()] == [self.user.id]

        genotypes = self.genomes[0].get_genotypes()

        assert genotypes.count() == 1

    def test_3_genomes_upload_ok(self):
        self.browser.visit('/genome/upload')
        default = {'file_format': Genome.FILE_FORMAT_VCF,
                   'population': POPULATION_UNKNOWN,
                   'sex': Genome.SEX_UNKNOWN}

        self.browser.attach_file('upload_files', os.path.join(settings.TEST_DATA_DIR, 'test_vcf42.vcf'))
        self.browser.fill_form(default)
        self.browser.find_by_name('submit').click()
        self.genomes = Genome.objects.filter(owner=self.user)
        assert len(self.genomes) == 1

        self.browser.attach_file('upload_files', os.path.join(settings.TEST_DATA_DIR, 'test_vcf42.vcf'))
        self.browser.fill_form(default)
        self.browser.find_by_name('submit').click()
        self.genomes = Genome.objects.filter(owner=self.user)
        assert len(self.genomes) == 2

        self.browser.attach_file('upload_files', os.path.join(settings.TEST_DATA_DIR, 'test_vcf42.vcf'))
        self.browser.fill_form(default)
        self.browser.find_by_name('submit').click()
        self.genomes = Genome.objects.filter(owner=self.user)
        assert len(self.genomes) == 3

        for genome in self.genomes:
            for owner in genome.readers.all():
                assert owner.id == self.user.id

    def test_invalid_genome_file_should_fail_upload(self):
        pass

    def test_genome_delete_ok(self):
        # TODO: DRY
        self.browser.visit('/genome/upload')
        self.browser.attach_file('upload_files', os.path.join(settings.TEST_DATA_DIR, 'test_vcf42.vcf'))
        self.browser.select('file_format', Genome.FILE_FORMAT_VCF)
        self.browser.select('population', POPULATION_UNKNOWN)
        self.browser.select('sex', Genome.SEX_UNKNOWN)
        self.browser.find_by_name('submit').click()

        self.genomes = [Genome.objects.get(owner=self.user)]

        # FIXME: #click raise NotImplementedError...
        # self.browser.find_by_id('delete-yes-' + str(self.genomes[0].id)).first.click()
        pass


    def test_not_exist_genome_should_fail_delete(self):
        # TODO:
        pass

    def test_genome_status_ok(self):
        # TODO: DRY
        self.browser.visit('/genome/upload')
        self.browser.attach_file('upload_files', os.path.join(settings.TEST_DATA_DIR, 'test_vcf42.vcf'))
        self.browser.select('file_format', Genome.FILE_FORMAT_VCF)
        self.browser.select('population', POPULATION_UNKNOWN)
        self.browser.select('sex', Genome.SEX_UNKNOWN)
        self.browser.find_by_name('submit').click()

        self.genomes = [Genome.objects.get(owner=self.user)]

        self.browser.visit('/genome/status')
        response = json.loads(self.browser.html)
        expected = {'status': 'ok',
                    'error_message': '',
                    'genome_info': {str(self.genomes[0].id): 100}}

        assert response == expected

    def test_genome_status_error(self):
        # TODO:
        pass
