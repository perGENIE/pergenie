from django.test import TestCase

from splinter import Browser

from apps.authentication.models import User
from .models import Genome


class GenomeBrowserTestCase(TestCase):
    def setUp(self):
        self.browser = Browser('django')

        # TODO: DRY
        self.test_user_id = 'test-user@pergenie.org'
        self.test_user_password = 'test-user-password'
        self.user = User.objects.create_user(self.test_user_id,
                                             self.test_user_password)
        self.user.is_active = True
        self.user.save()
        self.browser.visit('/login')
        self.browser.fill('email', self.test_user_id)
        self.browser.fill('password', self.test_user_password)
        self.browser.find_by_name('submit').click()

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
        self.browser.attach_file('upload_files', '/Users/k-numakura/Documents/perGENIE-private/pergenie/apps/genome/test_genome_file.txt')
        self.browser.select('file_format', Genome.FILE_FORMAT_VCF)
        self.browser.select('population', Genome.POPULATION_UNKNOWN)
        self.browser.select('sex', Genome.SEX_UNKNOWN)
        self.browser.find_by_name('submit').click()

        # TODO: celery job => stub

        pass

    def test_invalid_genome_file_should_fail_upload(self):
        pass

    def test_genome_delete_ok(self):
        self.browser.visit('/genome/upload')
        self.browser.attach_file('upload_files', '/Users/k-numakura/Documents/perGENIE-private/pergenie/apps/genome/test_genome_file.txt')
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

    # def test_celery_job_add(self):
    #     """Check if celery-job works

    #     * if fails with `error: [Errno 61] Connection refused]`, rabbitmq-server may not be working
    #     * if fails with `AssertionError: False != True`, celery may not be working

    #     """
    #     from lib.tasks import add
    #     from time import sleep

    #     r = add.delay(5, 5)
    #     sleep(1)

    #     self.failUnlessEqual(r.successful(), True)
    #     self.failUnlessEqual(r.result, 10)
