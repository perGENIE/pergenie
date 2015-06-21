from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings

from splinter import Browser

from test import MongoTestCase
from apps.authentication.models import User
from .models import Genome
from .tasks import ping


class GenomeBrowserTestCase(MongoTestCase):
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

    @override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                       CELERY_ALWAYS_EAGER=True,
                       BROKER_BACKEND='memory')
    def test_celery_task_ping_ok(self):
        result = ping.delay()
        assert result.successful() == True
        assert result.result == 'pong'

    def test_mongo_dummy_db_ok(self):
        dummy_collection = self.mongo_dummy_db['dummy']
        dummy_collection.insert_one({'ping': 'pong'})
        assert dummy_collection.find_one()['ping'] == 'pong'
