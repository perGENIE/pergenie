import subprocess
from pymongo import MongoClient
from django.conf import settings


def projection(info):
    pca_snps = []

    with MongoClient(host=settings.MONGO_URI) as connection:
        db = connection['pergenie']
        variants = db['variants'][info['user_id']][info['name']]

        user_snps = variants.find({'rs': {'$in': pca_snps}})
        user_bits = list()
        for snp in pca_snps:
            rec = user_snps.get(snp)
            if rec:
                user_bits.append(geno2bit(rec))
            else:
                # missing value...
                user_bits.append('-1')

        cmd = ['Rscript', 'project.r', '1000genomes.global.subsnps.csv'] + ' '.join(user_bits)
        result = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].split()[0]

        return result
