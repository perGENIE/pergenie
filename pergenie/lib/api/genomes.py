import sys, os
from pymongo import MongoClient
from django.conf import settings
from lib.mysql.bioq import Bioq
from lib.mongo.mutate_fasta import MutateFasta
m = MutateFasta(settings.PATH_TO_REFERENCE_FASTA)
from lib.api.gwascatalog import GWASCatalog
gwascatalog = GWASCatalog()
from utils import clogging
log = clogging.getColorLogger(__name__)


class Genomes(object):
    def __init__(self):
        self.db_select = settings.DB_SELECT['genomes']
        self.bq = Bioq(settings.DATABASES['bioq']['HOST'],
                       settings.DATABASES['bioq']['USER'],
                       settings.DATABASES['bioq']['PASSWORD'],
                       settings.DATABASES['bioq']['NAME'])

    def get_genotypes(self, user_id, file_name, file_format, locs, loctype='rs'):
        """
        Get genotypes of a user's genome file.
        Args:
          user_id:
          file_name:
          file_format:
          locs: a list of locations. locations are chrpos(int) or rsid(int).
          loctype: 'chrpos' or 'rs'

        Returns:
          a dict: {loc: genotype}

        Example:
          >>> get_genotypes('knmkr@pergenie.org', 'genome_1.vcf', 'vcf_whole_genome', [100,200], 'rs')
          {100: 'GG', 200: 'AT'}
        """
        assert loctype in ('rs', 'chrpos')
        genotypes = dict()
        locs = list(set(locs))

        if self.db_select == 'mongodb':
            with MongoClient(host=settings.MONGO_URI) as c:
                variants = c['pergenie']['variants'][user_id][file_name]
                records = variants.find({loctype: {'$in': locs}})

        if records:
            for record in records:
                genotypes.update({record[loctype]: record['genotype']})

        for loc in locs:
            if not loc in genotypes:
                genotypes.update({loc: self._ref_or_na(loc, loctype, file_format)})

        return genotypes

    def _ref_or_na(self, loc, loctype, file_format, ref=None):
        """
        Determine if genotype is `reference` or `N/A`.
        Args:
          loc: genomic location
          loctype: 'chrpos' or 'rs'
          file_format:

        Returns:
          genotype: 'XX'

        Example:
          >>> _ref_or_na(100, 'rs', 'andme')
          'na'  # N/A in SNP array
          >>> _ref_or_na(100, 'rs', 'vcf_whole_genome')
          'GG'  # reference genome is G
        """
        assert loctype == 'rs'  # TODO: add `chrpos`

        # If fileformat is SNP array, always `N/A`
        na = 'na'
        if file_format == 'andme':
            return na

        rec = list(gwascatalog.search_catalog_by_query(loc, 'rs'))
        if rec:
            rec = rec[0]
        else:
            log.warn('gwascatalog record not found: loc:%s loctype%s' % (loc, loctype))
            return na

        # Try to get `ref`
        if not ref:
            ref = self.bq.get_ref(loc)
            if not ref:
                ref = rec['ref']
                if not ref:
                    ref = na
                    log.warn('ref not found: loc:%s loctype%s' % (loc, loctype))

        # Cases for each fileformat
        if file_format == 'vcf_whole_genome':
            return ref * 2
        elif file_format == 'vcf_exome_truseq':
            if rec['is_in_truseq']:
                return ref * 2
            else:
                return na
        elif file_format == 'vcf_exome_iontargetseq':
            if rec['is_in_iontargetseq']:
                return ref * 2
            else:
                return na

    def get_data_infos(self, user_id):
        if user_id.startswith(settings.DEMO_USER_ID): user_id = settings.DEMO_USER_ID

        if self.db_select == 'mongodb':
            with MongoClient(host=settings.MONGO_URI) as c:
                data_info = c['pergenie']['data_info']
                infos = list(data_info.find({'user_id': user_id}))

        return infos

    def get_data_info(self, user_id, file_name):
        if user_id.startswith(settings.DEMO_USER_ID): user_id = settings.DEMO_USER_ID

        if self.db_select == 'mongodb':
            with MongoClient(host=settings.MONGO_URI) as c:
                data_info = c['pergenie']['data_info']
                info = data_info.find_one({'user_id': user_id, 'name': file_name})

        return info
