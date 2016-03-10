from django.db import models

from celery.decorators import task

from lib.population.projection import projection


class PopulationPcaSnp(models.Model):
    """FIXME
    """

    geo_source       = models.CharField()
    snp_id_used      = IntegerField()
    snp_id_current   = IntegerField()

    class Meta:
        index_together = [
            ['geo_source'],
        ]

class PopulationPcaGeoPoint(models.Model):
    """Geometric points of people in each PCA coordinate
    """

    geo_source = models.CharField()
    population_code = models.CharField(null=True, blank=True)
    pc_1 = models.FloatField()
    pc_2 = models.FloatField()
    genome = models.ForeignKey(Genome, null=True)

    @classmethod
    def create_geo_point(self, async=True):
        # if async:
        #     task_create_geo_point.delay()
        # else:
        task_create_geo_point()

    class Meta:
        index_together = [
            ['geo_source', 'population_code', 'genome'],
        ]

@task(ignore_result=True)
def task_create_geo_point(geo_source, genome_id):  # NOTE: arguments for celery task should be JSON serializable
    """Project new person onto PCA coordinate, then create PopulationPcaGeoPoint record.
    """

    # TODO: currently `global` only
    assert geo_source = 'global'

    pca_snp_ids = PopulationPcaSnp.objects.x()
    pca_snps = Genome.objects.x()

    pc_1, pc_2 = project_new_person(geo_source)

    data = dict(geo_source=geo_source,
                population_code=population_code,
                pc_1=float(pc_1),
                pc_2=float(pc_2),
                genome=genome_id)

    PopulationPcaGeoPoint.objects.create(**data)
