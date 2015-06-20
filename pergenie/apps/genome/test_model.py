from django.test import TestCase

from apps.authentication.models import User
from .models import Genome


class GenomeModelTestCase(TestCase):
    def setUp(self):
        self.test_user_id = 'test-user@pergenie.org'
        self.test_user_password = 'test-user-password'
        self.user = User.objects.create_user(self.test_user_id,
                                             self.test_user_password)
        self.user.is_active = True
        self.user.save()

    def test_genome_create_ok(self):
        genome = Genome(file_name='file_name.vcf',
                        display_name='display name',
                        file_format=Genome.FILE_FORMAT_VCF,
                        population=Genome.POPULATION_UNKNOWN,
                        sex=Genome.SEX_UNKNOWN)
        genome.save()
        genome.owners.add(self.user)
        genome.readers.add(self.user)

        records = Genome.objects.filter(id=genome.id)

        assert len(records) == 1
        assert records[0].file_name == 'file_name.vcf'
        assert records[0].display_name == 'display name'
        assert records[0].file_format == Genome.FILE_FORMAT_VCF
        assert records[0].population == Genome.POPULATION_UNKNOWN
        assert records[0].sex == Genome.SEX_UNKNOWN
        assert [x.id for x in records[0].owners.all()] == [self.user.id]
        assert [x.id for x in records[0].readers.all()] == [self.user.id]

    def test_invalid_params_should_fail_create(self):
        pass
