#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb as mdb
import sys

class Bioq(object):
    def __init__(self, host, username, password, dbname):
        self.host = host
        self.username = username
        self.password = password
        self.dbname = dbname
        # self.merged = {121909559: 121909548}

    def _sql(self, sql):
        con = mdb.connect(self.host, self.username, self.password, self.dbname)
        with con:
            cur = con.cursor(mdb.cursors.DictCursor)
            cur.execute(sql)
            rows = cur.fetchall()
            return rows

    def _allele_freqs(self, rs):
        # rs = self.merged.get(rs, rs)
        rows = self._sql("select * from _loc_allele_freqs where snp_id = '%s'" % rs)
        return rows

    def _snp_summary(self, rs):
        # rs = self.merged.get(rs, rs)
        row = self._sql("select * from _loc_snp_summary where snp_id = '%s' limit 1" % rs)
        if not row:
            print >>sys.stderr, '{0} not found'.format(rs)

        return row[0] if row else None

    def _SNPContigLoc(self, rs):
        row = self._sql("select * from b137_SNPContigLoc where snp_type = 'rs' && snp_id = %s limit 1" % rs)
        if not row:
            print >>sys.stderr, '{0} not found'.format(rs)

        return row[0] if row else None

    def get_allele_freqs(self, rs):
        rows = self._allele_freqs(rs)

        allele_freqs = {'Asian':{}, 'European':{}, 'African':{}, 'Japanese': {}}

        # Consider allele strands
        rev = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}
        for row in rows:
            _snp_contig = self._SNPContigLoc(rs)
            if not _snp_contig:
                return dict(), set()
            if _snp_contig['orientation'] == 1:
                row.update({'allele': rev.get(row['allele'])})

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
        row = self._sql("select * from GeneIdToName where gene_id = '%s' limit 1" % gene_id)
        return row[0] if row else None

    def get_gene_id(self, gene_symbol):
        # TODO:
        pass

    def get_rs(self, chrom, pos):
        _chr2num = {'X': '23', 'Y': '24', 'MT': '25', 'M': '25'}
        chrpos = _chr2num.get(chrom, chrom).zfill(2) + str(pos).zfill(9)

        row = self._sql("select * from _loc_snp_summary where pos_global = %s limit 1" % chrpos)
        # if not row:
        #     print >>sys.stderr, 'pos_global {0} not found'.format(chrpos)

        if row:
            return int(row[0]['snp_id'])
        else:
            return None
