from collections import defaultdict
from pymongo import MongoClient
from django.conf import settings
from lib.mysql.bioq import Bioq

def get_mycatalog():
    with MongoClient(host=settings.MONGO_URI) as c:
        db = c['pergenie']
        mycatalog = db['mycatalog']

        return list(mycatalog.find())


def get_freq(rsid, user_id):
    """
    Get genotype freq. and allele freq. of
    genome files of a user.
    """

    bq= Bioq(settings.DATABASES['bioq']['HOST'],
             settings.DATABASES['bioq']['USER'],
             settings.DATABASES['bioq']['PASSWORD'],
             settings.DATABASES['bioq']['NAME'])

    with MongoClient(host=settings.MONGO_URI) as c:
        db = c['pergenie']
        data_info = db['data_info']

        genotypes = defaultdict(int)
        alleles = defaultdict(int)
        user_datas = list(data_info.find({'user_id': user_id}))
        for data in user_datas:
            rs = int(rsid.replace('rs', ''))
            variants = db['variants'][user_id][data['name']]
            record = variants.find_one({'rs': rs})

            if record:
                genotypes[record['genotype']] += 1
                alleles[record['genotype'][0]] += 1
                alleles[record['genotype'][1]] += 1
            else:
                if data['file_format'] == 'andme':
                    pass

                elif data['file_format'] == 'vcf_whole_genome':
                    ref = bq.get_ref(rs)

                    if not ref: ref = 'ref'  # FIXME:
                    genotypes[ref+ref] += 1
                    alleles[ref] += 2

                elif data['file_format'] == 'vcf_exome_truseq':
                    pass  # FIXME: need to check if this rs is in exome region

        return (dict(genotypes),dict(alleles))
