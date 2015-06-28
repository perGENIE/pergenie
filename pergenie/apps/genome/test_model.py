import os
import shutil

from django.test import TestCase
from django.test.utils import override_settings
from django.conf import settings
from django.utils.translation import ugettext as _

from pergenie.mongo import mongo_db
from apps.authentication.models import User
from .models import Genome


@override_settings(CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
                   CELERY_ALWAYS_EAGER=True,
                   BROKER_BACKEND='memory')
class GenomeModelTestCase(TestCase):
    def setUp(self):
        self.test_user_id = 'test-user@pergenie.org'
        self.test_user_password = 'test-user-password'
        self.user = User.objects.create_user(self.test_user_id,
                                             self.test_user_password)
        self.user.is_active = True
        self.user.save()
        self.genome = None

    def tearDown(self):
        if self.genome:
            self.genome.delete_genotypes()
            self.genome.delete()

    def test_genome_create_ok(self):
        # TODO: DRY
        self.genome = Genome(owner=self.user,
                             file_name='file_name.vcf',
                             display_name='display name',
                             file_format=Genome.FILE_FORMAT_VCF,
                             population=Genome.POPULATION_UNKNOWN,
                             sex=Genome.SEX_UNKNOWN)
        self.genome.save()
        self.genome.readers.add(self.user)

        records = Genome.objects.filter(id=self.genome.id)

        assert len(records) == 1
        assert records[0].file_name == 'file_name.vcf'
        assert records[0].display_name == 'display name'
        assert records[0].file_format == Genome.FILE_FORMAT_VCF
        assert records[0].population == Genome.POPULATION_UNKNOWN
        assert records[0].sex == Genome.SEX_UNKNOWN
        assert records[0].owner == self.user
        assert [x.id for x in records[0].readers.all()] == [self.user.id]

    def test_invalid_params_should_fail_create(self):
        pass

    def test_create_genotypes_ok(self):
        # TODO: DRY
        self.genome = Genome(owner=self.user,
                             file_name='file_name.vcf',
                             display_name='display name',
                             file_format=Genome.FILE_FORMAT_VCF,
                             population=Genome.POPULATION_UNKNOWN,
                             sex=Genome.SEX_UNKNOWN)
        self.genome.save()

        genome_file_dir = os.path.join(settings.UPLOAD_DIR, str(self.user.id))
        if not os.path.exists(genome_file_dir):
            os.makedirs(genome_file_dir)

        shutil.copyfile(src=os.path.join(settings.TEST_DATA_DIR, 'test_vcf42.vcf'),
                        dst=os.path.join(genome_file_dir, str(self.genome.id)))

        self.genome.create_genotypes()

        genome = Genome.objects.get(id=self.genome.id)
        genotypes = genome.get_genotypes()

        assert genome.status == 100
        assert genotypes.count() == 1
        assert genotypes.find_one({'rs': 6054257})['genotype'] == 'GG'

    def test_invalid_genome_file_should_fail_create_genotypes(self):
        # TODO: DRY
        self.genome = Genome(owner=self.user,
                             file_name='file_name.vcf',
                             display_name='display name',
                             file_format=Genome.FILE_FORMAT_VCF,
                             population=Genome.POPULATION_UNKNOWN,
                             sex=Genome.SEX_UNKNOWN)
        self.genome.save()

        genome_file_dir = os.path.join(settings.UPLOAD_DIR, str(self.user.id))
        if not os.path.exists(genome_file_dir):
            os.makedirs(genome_file_dir)

        shutil.copyfile(src=os.path.join(settings.TEST_DATA_DIR, 'test_invalid_vcf42.vcf'),
                        dst=os.path.join(genome_file_dir, str(self.genome.id)))

        self.genome.create_genotypes()

        genome = Genome.objects.get(id=self.genome.id)
        genotypes = genome.get_genotypes()

        assert genome.status == -1
        assert genome.error == _('Invalid genome file.')
