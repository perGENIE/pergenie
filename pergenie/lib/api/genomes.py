import sys, os
from pymongo import MongoClient
from django.conf import settings
from lib.mysql.bioq import Bioq
bq = Bioq(settings.DATABASES['bioq']['HOST'],
         settings.DATABASES['bioq']['USER'],
         settings.DATABASES['bioq']['PASSWORD'],
         settings.DATABASES['bioq']['NAME'])
from lib.mongo.mutate_fasta import MutateFasta
m = MutateFasta(settings.PATH_TO_REFERENCE_FASTA)
from lib.mongo.get_latest_catalog import get_latest_catalog

DB_TYPE = 'mongodb'


class Genomes(object):
    def __init__(self):
        # TODO: db select & settings
        pass

    def get_data_infos(user_id):
        if DB_TYPE == 'mongodb':
            with MongoClient(host=settings.MONGO_URI) as c:
                data_info = c['pergenie']['data_info']
                if user_id.startswith(settings.DEMO_USER_ID): user_id = settings.DEMO_USER_ID
                infos = list(data_info.find({'user_id': user_id}))

        return infos


    def get_genotypes(user_id, file_name, file_format, locs, loctype='rs'):
        """
        API for getting genotypes, with specified backend dbs.

        Args:
        user_id:
        file_name:
        file_format:
        locs: a list of locations. locations are chrpos(int) or rsid(int).
        loctype: 'chrpos' or 'rs'

        Retval:
        a dict of {loctype: genotype}
        """
        assert loctype in ('rs', 'chrpos')
        genotypes = dict()
        locs = list(set(locs))

        if DB_TYPE == 'mongodb':
            with MongoClient(host=settings.MONGO_URI) as c:
                variants = c['pergenie']['variants'][user_id][file_name]
                records = variants.find({loctype: {'$in': locs}})
                print 'list(records)', list(records)

                if records:
                    for record in records:
                        genotypes.update({record[loctype]: record['genotype']})

                for loc in locs:
                    if not loc in genotypes:
                        genotypes.update({loc: _ref_or_na(loc, loctype, file_format)})

        return genotypes


    def _ref_or_na(loc, loctype, file_format):
        na = 'na'
        if file_format == 'andme':
            return na

        # Try to get ref
        if loctype == 'chrpos':
            chrom, pos = bq._to_chrom_pos(loc)
            ref = m._slice_fasta(chrom, pos, pos)
        else:
            ref = bq.get_ref(loc, loctype=loctype)
            if not ref:
                # FIXME: API for search catalog
                catalog = get_latest_catalog()
                rec = catalog.find_one({'rs': loc})
                if rec:
                    ref = rec['ref']

        if ref:
            ref = ref * 2
        else:
            ref = na
            print >>sys.stderr, 'lib.utils.db.get_genotypes: _ref_or_na: %s %s not found' % (loctype, loc)

        if file_format == 'vcf_whole_genome':
            return ref
        elif file_format == 'vcf_exome_truseq':
            # FIXME:
            catalog = get_latest_catalog()
            rec = catalog.find_one({'rs': loc})
            if not rec:
                return na
            if rec['is_in_truseq']:
                return ref
            else:
                return na
