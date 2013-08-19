import sys, os
from collections import defaultdict
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

    def get_freq(self, user_id, locs, loctype='rs', rec=None):
        # Build query
        if type(locs) in (str, unicode, int):  # FIXME
            locs = [locs]
        locs = [int(str(loc).replace('rs', '')) for loc in locs]

        # Init frequency counter
        genotype_freq, allele_freq = dict(), dict()
        for loc in locs:
            rs = 'rs' + str(loc)
            genotype_freq[rs], allele_freq[rs] = defaultdict(int), defaultdict(int)

        # Count frequency
        for data in self.get_data_infos(user_id):
            genotype = self.get_genotypes(user_id, data['name'], data['file_format'], locs, rec=rec)

            for loc in locs:
                rs = 'rs' + str(loc)
                genotype_freq[rs][genotype[loc]] += 1

                if not genotype[loc] == 'na':
                    allele_freq[rs][genotype[loc][0]] += 1
                    allele_freq[rs][genotype[loc][1]] += 1

        # default dict to dict
        for loc in locs:
            rs = 'rs' + str(loc)
            genotype_freq[rs], allele_freq[rs] = dict(genotype_freq[rs]), dict(allele_freq[rs])

        return (genotype_freq, allele_freq)

    def get_genotypes(self, user_id, file_name, file_format, locs, loctype='rs', rec=None, check_ref_or_not=True):
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

        # Add ref or N/A
        for loc in locs:
            if not loc in genotypes:
                if rec:
                    genotypes.update({loc: self._ref_or_na(loc, loctype, file_format, rec=rec)})
                elif check_ref_or_not:
                    # FIXME:
                    genotypes.update({loc: self._ref_or_na(loc, loctype, file_format)})

        return genotypes

    def _ref_or_na(self, loc, loctype, file_format, rec=None):
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

        # If fileformat is SNP array, always `N/A`.
        na = 'na'
        if file_format == 'andme':
            log.debug('in andme region, but genotype is na')
            return na

        # If rec(gwascatalog record) is provided, use it. otherwise seach mongo.catalog.
        if not rec:
            rec = list(gwascatalog.search_catalog_by_query('rs%s' % loc, None))
            if rec:
                rec = rec[0]
            else:
                log.warn('gwascatalog record not found: loc: %s loctype: %s' % (loc, loctype))
                return na

        # Try to get ref(reference allele).
        ref = rec.get('ref')
        if not ref:
            log.debug('try to get allele of reference genome')
            ref = self.bq.get_ref_genome(loc, rec=rec)
            if not ref:
                ref = na
                log.warn('ref not found: loc: %s loctype: %s' % (loc, loctype))

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

    def search_data_info(self, user_id, query):
        """
        Example:
          query = {'rs': xxxx, 'genotype': 'XX'}

        Returns:
          # people who have genotypes of 'XX' for rs xxxx
          ['personA', 'personC']

        """
        people = set()

        if self.db_select == 'mongodb':
            with MongoClient(host=settings.MONGO_URI) as c:
                data_info = c['pergenie']['data_info']
                infos = list(data_info.find({'user_id': user_id}))
                for info in infos:
                    variants = c['pergenie']['variants'][user_id][info['name']]
                    records = list(variants.find(query))
                    if records:
                        people.update([info['name']])
        return list(people)
