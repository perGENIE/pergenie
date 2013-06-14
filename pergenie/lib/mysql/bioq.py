#!/usr/bin/env python
# -*- coding: utf-8 -*-

import MySQLdb as mdb

class Bioq(object):
    def __init__(self, host, username, password, dbname):
        self.host = host
        self.username = username
        self.password = password
        self.dbname = dbname

    def _sql(self, sql):
        con = mdb.connect(self.host, self.username, self.password, self.dbname)
        with con:
            cur = con.cursor(mdb.cursors.DictCursor)
            cur.execute(sql)
            rows = cur.fetchall()
            return rows

    def allele_freqs(self, rs):
        rows = self._sql("select * from _loc_allele_freqs where snp_id = '%s'" % rs)
        return rows

    def snp_summary(self, rs):
        rows = self._sql("select * from _loc_snp_summary where snp_id = '%s'" % rs)
        row = rows[0]
        return row
