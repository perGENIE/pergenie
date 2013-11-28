import sys, os
import subprocess
from pymongo import MongoClient
from django.conf import settings
from lib.api.genomes import Genomes
genomes = Genomes()
from utils import clogging
log = clogging.getColorLogger(__name__)

def projection(scale, info):
    _1000genomes = os.path.join(settings.BASE_DIR, 'lib', 'r', '1000genomes.{0}.subsnps.csv'.format(scale))

    with open(_1000genomes, 'r') as f:
        pca_snps = f.next().rstrip().split(',')[:-1]

    with MongoClient(host=settings.MONGO_URI) as connection:
        db = connection['pergenie']
        variants = genomes.get_variants(info['user_id'], info['name'])

        user_snps_list = variants.find({'rs': {'$in': [int(s[2:-2]) for s in pca_snps]}})
        user_snps = dict((data['rs'], data) for data in user_snps_list)
        user_bits = list()
        for snp in pca_snps:
            rec = user_snps.get(int(snp[2:-2]))  # "rs100GT" => 100
            if rec:
                # count alt alleles
                ref = snp[-2:-1]
                alt = snp[-1]
                ref_count = rec['genotype'].count(ref)
                alt_count = rec['genotype'].count(alt)
                if ref_count + alt_count != 2:
                    log.warn('ref_count + alt_count != 2, {0} {1}'.format(snp, rec))
                bit = {0:'-1', 1:'0', 2:'1'}[alt_count]
                user_bits.append(bit)
            else:
                # TODO: fill missing data with appropriate value
                user_bits.append('-1')

        cmd = ['Rscript', os.path.join(settings.BASE_DIR, 'lib', 'r', 'project.r'), _1000genomes] + user_bits + [info['name']]
        result = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].split()

        return [float(result[1]), float(result[2])]
