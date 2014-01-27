import MySQLdb as mdb
import sys
import string
from pprint import pprint as pp
from django.conf import settings
from lib.utils.deprecated_decorator import deprecated
from lib.mongo.mutate_fasta import MutateFasta
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Bioq(object):
    """
    dependancies:

    import following tables first:

    * GeneIdToName
    * _loc_allele_freqs
    * _loc_snp_summary
    * b137_SNPContigLoc

    """

    def __init__(self, host, username, password, dbname):
        self.host = host
        self.username = username
        self.password = password
        self.dbname = dbname
        # self.merged = {121909559: 121909548}

    def _sql(self, sql, param):
        conf = dict(user=self.username, passwd=self.password, db=self.dbname)
        if self.host.endswith('sock'): conf['unix_socket'] = self.host
        else: conf['host'] = self.host
        con = mdb.connect(**conf)

        with con:
            cur = con.cursor(mdb.cursors.DictCursor)
            cur.execute(sql, param)
            rows = cur.fetchall()
            return rows

    def _allele_freqs(self, rs):
        rows = self._sql("select * from _loc_allele_freqs where snp_id = '%s'", rs)
        return rows

    def _snp_summary(self, rs, limit_1=True):
        raw_query = "select * from _loc_snp_summary where snp_id in (%s)"
        if type(rs) in (str, unicode, int):
            rs = [rs]
        _in = ','.join(list(map(lambda x: '%s', rs)))  # `%s,%s,%s ...`
        raw_query = raw_query % _in  # `select * ... (%s,%s,%s)`

        if limit_1:
            raw_query += ' limit 1'
            row = self._sql(raw_query, rs)
            return row[0] if row else None
        else:
            row = self._sql(raw_query, rs)
            return row

    def _SNPContigLoc(self, rs):
        row = self._sql("select * from b137_SNPContigLoc where snp_type = 'rs' && snp_id = %s limit 1", rs)
        if not row:
            log.warn('{0} not found'.format(rs))

        return row[0] if row else None

    def get_ref(self, rs):
        """
        NOTICE:
          'allele' in `b137_SNPContigLoc` is `+ orientation` (TODO: confirm this)
        """
        _snp_contig = self._SNPContigLoc(rs)
        if not _snp_contig:
            return None
        # FIXME:
        if _snp_contig['orientation'] == 1:
            _snp_contig['allele'] = _snp_contig['allele'].translate(string.maketrans('ATGC', 'TACG'))
        return _snp_contig['allele']

    def get_ref_genome(self, rs, rec=None):
        """
        NOTICE:
          `allele` in `b137_SNPContigLoc` is not always equal to allele of reference genome.
          (reference genome may have SNPs!)
          So, if you want to get allele of reference genome,
          use this method. Do not use `.get_ref()`.
        """

        if type(rs) in (str, unicode):
            rs = int(rs.replace('rs', ''))

        if rec:
            chr_id = rec.get('chr_id')
            chr_pos = rec.get('chr_pos')

        if not rec or (chr_id is None) or (chr_pos is None):
            pos_global = self.get_pos_global(rs)['rs' + str(rs)]
            if not pos_global:
                return None

            chr_id = int(pos_global[0:2])
            chr_pos = int(pos_global[2:])

        m = MutateFasta(settings.PATH_TO_REFERENCE_FASTA)
        ref = m._slice_fasta({23:'X', 24:'Y', 25:'M'}.get(chr_id, str(chr_id)), chr_pos, chr_pos)

        return ref

    @deprecated()
    def get_allele_freqs(self, rs, population='unkown'):
        """
        """

        rows = self._allele_freqs(rs)

        allele_freqs = {'Asian':{}, 'European':{}, 'African':{}, 'Japanese': {}}

        #
        # WARNING!!!
        # This allele strand fixing is buggy. Altanatively, use lib.mysql.snps.Snps.
        #
        # Consider allele strands
        for row in rows:
            _snp_contig = self._SNPContigLoc(rs)
            if not _snp_contig:
                return dict(), set()
            if _snp_contig['orientation'] == 1:
                rev = row['allele'].translate(string.maketrans('ATGC', 'TACG'))
                row.update({'allele': rev})

        # TODO: write more simply...
        # First scan
        for row in rows:
            if row['loc_pop_id'] == 'HapMap-CEU':
                allele_freqs['European'][row['allele']] = row

            elif row['loc_pop_id'] == 'HapMap-JPT':
                allele_freqs['Japanese'][row['allele']] = row

            # ok?
            elif row['loc_pop_id'] in ('HapMap-HCB', 'HapMap-CHB', 'HapMap-JPT'):
                allele_freqs['Asian'][row['allele']] = row

            # ok?
            elif row['loc_pop_id'] == 'HapMap-YRI':
                allele_freqs['African'][row['allele']] = row

            else:
                pass

        # Second scan
        for row in rows:
            if not allele_freqs['European']:
                if row['loc_pop_id'] == 'pilot_1_CEU_low_coverage_panel':
                    allele_freqs['European'][row['allele']] = row

            if not allele_freqs['Asian']:
                if row['loc_pop_id'] == 'pilot_1_CHB+JPT_low_coverage_panel':
                    allele_freqs['Asian'][row['allele']] = row

            if not allele_freqs['African']:
                if row['loc_pop_id'] == 'pilot_1_YRI_low_coverage_panel':
                    allele_freqs['African'][row['allele']] = row
            else:
                pass

        # # Third scan...?

        # Uniq alleles
        alleles = set()
        for pop, allele_freq in allele_freqs.items():
            alleles.update([allele for allele in allele_freq.keys()])

        return allele_freqs, alleles

    def get_snp_summary(self, rs):
        # TODO:
        return self._snp_summary(rs)

    def get_gene_symbol(self, gene_id):
        row = self._sql("select * from GeneIdToName where gene_id = '%s' limit 1", gene_id)
        return row[0] if row else None

    def get_gene_id(self, gene_symbol):
        # TODO:
        pass

    def get_rs(self, chrom, pos):
        chrom = chrom.replace('chr', '')
        _chr2num = {'X': '23', 'Y': '24', 'MT': '25', 'M': '25'}
        chrpos = _chr2num.get(chrom, chrom).zfill(2) + str(pos).zfill(9)

        row = self._sql("select * from _loc_snp_summary where pos_global = %s limit 1", chrpos)

        if row:
            return int(row[0]['snp_id'])
        else:
            return None

    def get_pos_global(self, rs):
        records = self._snp_summary(rs, limit_1=False)

        rs2pos_global = {}
        if not records:
            rs2pos_global.update({'rs'+str(rs): None})
        else:
            for rec in records:
                if rec['pos_global'] is not None:
                    rs2pos_global.update({'rs'+str(rec['snp_id']): str(rec['pos_global']).zfill(11)})
                else:
                    rs2pos_global.update({'rs'+str(rec['snp_id']): None})

        return rs2pos_global
