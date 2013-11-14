# -*- coding: utf-8 -*-

import sys
import argparse
import MySQLdb as mdb

# FIXME: avoid hardcoding
USERNAME = 'root'
PASSWORD = ''
DBNAME = 'liftover'

table = 'hg18LiftToHg19'

def init_db(**kwargs):
    """Init database.
    """

    con = mdb.connect(user=USERNAME, passwd=PASSWORD, db=DBNAME)
    with con:
        cur = con.cursor(mdb.cursors.DictCursor)

        # Init
        cur.execute("""DROP TABLE IF EXISTS hg18LiftToHg19""")

        # Table schema
        cur.execute("""CREATE TABLE hg18LiftToHg19 (
        `hg18chrom` varchar(2) default NULL,
        `hg18pos` bigint(11) default NULL,
        `hg19chrom` varchar(2) default NULL,
        `hg19pos` bigint(11) default NULL,
        KEY `i_hg18_chrom_pos` (`hg18chrom`,`hg18pos`),
        KEY `i_hg19_chrom_pos` (`hg19chrom`,`hg19pos`)
        )""")


def load_data(hg18tohg19, **kwargs):
    con = mdb.connect(user=USERNAME, passwd=PASSWORD, db=DBNAME)
    with con:
        cur = con.cursor(mdb.cursors.DictCursor)

        # Load data
        print 'updating hg18...'
        with open(hg18tohg19) as fin:
            for line in fin:
                hg18chrom, hg18pos, hg19pos = line.rstrip().split('\t')

                hg18chrom, hg18pos = hg18chrom.replace('chr', ''), int(hg18pos)

                if hg19pos == '.':
                    hg19chrom, hg19pos = None, None
                else:
                    hg19chrom, hg19pos = hg18chrom, int(hg19pos)

                cur.execute("""INSERT INTO hg18LiftToHg19 VALUES (%s, %s, %s, %s)""", (hg18chrom, hg18pos, hg19chrom, hg19pos,))

        print 'done'

        # Count
        cur.execute("""SELECT COUNT(*) FROM hg18LiftToHg19""")
        res = cur.fetchone()
        print res


def search_db(version_from, version_to, chrom, pos, **kwargs):
    con = mdb.connect(user=USERNAME, passwd=PASSWORD, db=DBNAME)
    with con:
        cur = con.cursor(mdb.cursors.DictCursor)

        # FIXME: avoid hardcoding
        if version_from == 'hg18':
            cur.execute("""SELECT * FROM hg18LiftToHg19 WHERE hg18chrom=%s and hg18pos=%s""", (str(chrom), int(pos),))
        # if version_from == 'hg19':
        #     cur.execute("""SELECT * FROM liftover WHERE hg19chrom=%s and hg19pos=%s""", (str(chrom), int(pos),))

        row = cur.fetchone()
        rec = [row[version_to + 'chrom'], int(row[version_to + 'pos'])] if row else []

        # If called by main(), print result
        if 'func' in kwargs:
            print rec

        return rec


def _main():
    parser = argparse.ArgumentParser(description='')
    subparsers = parser.add_subparsers()

    parser_init_db = subparsers.add_parser('init')
    parser_init_db.set_defaults(func=init_db)

    parser_init_db = subparsers.add_parser('load')
    parser_init_db.add_argument('hg18tohg19')
    parser_init_db.set_defaults(func=load_data)

    parser_search_db = subparsers.add_parser('search')
    parser_search_db.add_argument('version_from', choices=['hg18', 'hg19'])
    parser_search_db.add_argument('version_to', choices=['hg18', 'hg19'])
    parser_search_db.add_argument('chrom', choices=['1','2','3','4','5','6','7','8','9','10',
                                                    '11','12','13','14','15','16','17','18','19','20',
                                                    '21','22','X','Y','M','MT'])
    parser_search_db.add_argument('pos', type=int)
    parser_search_db.set_defaults(func=search_db)

    args = parser.parse_args()
    args.func(**vars(args))


if __name__ == '__main__':
    _main()
