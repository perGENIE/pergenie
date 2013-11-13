# -*- coding: utf-8 -*-

import sys
import argparse
import MySQLdb as mdb

# FIXME: avoid hardcoding
USERNAME = 'root'
PASSWORD = ''
DBNAME = 'liftover'


def init_db(hg18sample, hg19sample, **kwargs):
    """Init database.

    Create table `liftover`, then load rsIDs, chroms, and positions.

    - hg18sample: 23andme format genotype data
    - hg19sample: 23andme format genotype data
    """

    con = mdb.connect(user=USERNAME, passwd=PASSWORD, db=DBNAME)
    with con:
        cur = con.cursor(mdb.cursors.DictCursor)

        # Init
        cur.execute("""DROP TABLE IF EXISTS `liftover`""")

        # Table schema
        cur.execute("""CREATE TABLE `liftover` (
        `snp_id` int(11) NOT NULL default '0',
        `hg18chrom` varchar(2) default NULL,
        `hg18pos` bigint(11) default NULL,
        `hg19chrom` varchar(2) default NULL,
        `hg19pos` bigint(11) default NULL,
        PRIMARY KEY  (`snp_id`),
        KEY `i_hg18_chrom_pos` (`hg18chrom`,`hg18pos`),
        KEY `i_hg19_chrom_pos` (`hg19chrom`,`hg19pos`)
        )""")

        # Load data
        print 'updating hg18...'
        with open(hg18sample) as fin:
            for line in fin:
                if line.startswith('#'): continue
                rs, chrom, pos, genotype = parse_23andme(line.split('\t'))

                if rs:
                    cur.execute("""INSERT IGNORE INTO liftover VALUES (%s, null, null, null, null)""", (rs,))  # rsid
                    cur.execute("""UPDATE liftover SET hg18chrom=%s, hg18pos=%s WHERE snp_id=%s""", (chrom, pos, rs,))  # update hg18


        print 'updating hg19...'
        with open(hg19sample) as fin:
            for line in fin:
                if line.startswith('#'): continue
                rs, chrom, pos, genotype = parse_23andme(line.split('\t'))

                if rs:
                    cur.execute("""INSERT IGNORE INTO liftover VALUES (%s, null, null, null, null)""", (rs,))  # rsid
                    cur.execute("""UPDATE liftover SET hg19chrom=%s, hg19pos=%s WHERE snp_id=%s""", (chrom, pos, rs,))  # update hg19

        print 'done'

        # Count
        cur.execute("""SELECT COUNT(*) FROM liftover""")
        res = cur.fetchone()
        print res


def search_db(version_from, version_to, chrom, pos, **kwargs):
    con = mdb.connect(user=USERNAME, passwd=PASSWORD, db=DBNAME)
    with con:
        cur = con.cursor(mdb.cursors.DictCursor)

        # FIXME: avoid hardcoding
        if version_from == 'hg18':
            cur.execute("""SELECT * FROM liftover WHERE hg18chrom=%s and hg18pos=%s""", (str(chrom), int(pos),))
        if version_from == 'hg19':
            cur.execute("""SELECT * FROM liftover WHERE hg19chrom=%s and hg19pos=%s""", (str(chrom), int(pos),))

        row = cur.fetchone()
        rec = [row[version_to + 'chrom'], int(row[version_to + 'pos'])] if row else []

        # If called by main(), print result
        if 'func' in kwargs:
            print rec

        return rec


def parse_23andme(record):
    _rs, _chrom, _pos, _genotype = record

    try:
        rs = int(_rs.replace('rs', ''))  # int
    except ValueError:
        rs = None
    chrom = _chrom  # str
    pos = int(_pos)  # int
    genotype = _genotype  # str
    return rs, chrom, pos, genotype


def _main():
    parser = argparse.ArgumentParser(description='')
    subparsers = parser.add_subparsers()

    parser_init_db = subparsers.add_parser('init')
    parser_init_db.add_argument('hg18sample')
    parser_init_db.add_argument('hg19sample')
    parser_init_db.set_defaults(func=init_db)

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
