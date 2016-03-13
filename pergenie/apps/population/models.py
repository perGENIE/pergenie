import os

from django.db import models
from django.conf import settings
from celery.decorators import task

from apps.genome.models import Genome, Genotype
from lib.population.projection import project_new_person


class PopulationPcaGeoPoint(models.Model):
    """Geometric points of people in each PCA coordinate
    """

    src  = models.CharField(max_length=128)
    pc_1 = models.FloatField(null=True)
    pc_2 = models.FloatField(null=True)
    genome = models.ForeignKey(Genome, null=True)
    population_code = models.CharField(max_length=16, null=True, blank=True)

    def create_geo_point(self, async=True):
        if async:
            task_create_geo_point.delay(self.id, str(self.genome.id))
        else:
            task_create_geo_point(self.id, str(self.genome.id))

    class Meta:
        unique_together = ('src', 'genome')
        index_together = [
            ['src', 'population_code', 'genome'],
        ]

# NOTE: arguments for celery task should be JSON serializable
@task(ignore_result=True)
def task_create_geo_point(geo_point_id, genome_id):
    """Project new person onto PCA coordinate, then create PopulationPcaGeoPoint record.
    """

    geo_point = PopulationPcaGeoPoint.objects.get(id=geo_point_id)
    genome = Genome.objects.get(id=genome_id)

    # Load Population PCA SNPs
    population = 'global'
    csv = os.path.join(settings.BASE_DIR, 'lib', 'population', 'csv', '1000genomes.{}.subsnps.csv'.format(population))
    pca_snps = []
    with open(csv, 'r') as fin:
        for i, line in enumerate(fin):
            if i == 0:
                for snp in line.split(',')[:-1]:
                    pca_snps.append(dict(src=os.path.basename(csv),
                                        snp_id_current=int(snp[2:-2]),  # FIXME: Need to update rs id
                                        ref=snp[-2:-1],
                                        alt=snp[-1]))
                break

    # Create SNPs matrix
    pca_snp_ids = [x['snp_id_current'] for x in pca_snps]
    genotypes = Genotype.objects.filter(genome__id=genome.id, rs_id_current__in=pca_snp_ids)
    genotype_bits = list()
    for snp in pca_snps:
        genotype = genotypes.filter(rs_id_current=snp['snp_id_current'])

        if not genotype:
            bit = '-1'  # FIXME: Fill missing data with appropriate value
        else:
            # Count alt alleles
            alt = snp['alt']
            alt_count = 0
            for allele in genotype[0].genotype:
                if allele == alt:
                    alt_count += 1

            bit = {0: '-1', 1: '0', 2: '1'}[alt_count]
        genotype_bits.append(bit)

    # Projection
    pc_1, pc_2 = project_new_person(csv, genotype_bits, genome.display_name.replace(' ', '_'))
    data = dict(src=os.path.basename(csv),
                pc_1=float(pc_1),
                pc_2=float(pc_2),
                genome=genome)
    PopulationPcaGeoPoint.objects.create(**data)
