import os

from django.conf import settings

from utils import clogging
log = clogging.getColorLogger(__name__)


def pca_snp_ids():
    """Returns PCA SNP ids from the header line of `lib/population/csv/1000genomes.global.subsnps.csv`
    """

    # FIXME: Need to update rs id
    src = os.path.join(settings.BASE_DIR, 'lib', 'population', 'csv', '1000genomes.global.subsnps.csv')
    with open(src) as fin:
        for line in fin:
            snps = line.strip().split(',')[0:-1]
            snp_ids = [int(snp[2:-2]) for snp in snps]
            break

    return snp_ids
