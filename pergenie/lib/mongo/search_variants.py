#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import argparse
import pymongo

# import colors
from search_catalog import search_catalog_by_query
from get_latest_catalog import get_latest_catalog


def search_variants(user_id, file_name, query, query_type=None, mongo_port=27017):
    with pymongo.Connection(port=mongo_port) as connection:
        catalog = get_latest_catalog(port=mongo_port)

        variants = connection['pergenie']['variants'][user_id][file_name]

        catalog_records = search_catalog_by_query(query, query_type=query_type).sort('trait', 1)

        tmp_catalog_map = {}
        found_id = 0
        snps_all = set()
        for record in catalog_records:
            snps_all.update([record['snps']])

            # snps = ', '.join(map(str, record['snps']))
            reported_genes = ', '.join([gene['gene_symbol'] for gene in record['reported_genes']])
            mapped_genes = ', '.join([gene['gene_symbol'] for gene in record['mapped_genes']])

            found_id += 1
            tmp_catalog_map[found_id] = record
            tmp_catalog_map[found_id].update({'rs':record['snps'],
                                              'reported_genes':reported_genes,
                                              'mapped_genes':mapped_genes,

                                              'chr':record['chr_id'],
                                              'freq':record['risk_allele_frequency'],

                                              'added':record['added'].date(),
                                              'date':record['date'].date(),

                                              'dbsnp_link':'http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs='+str(record['snps']),
                                              'pubmed_link':'http://www.ncbi.nlm.nih.gov/pubmed/'+str(record['pubmed_id'])
                                              })

        variants_records = variants.find({'rs': {'$in': list(snps_all)}})

        # in catalog & in variants
        tmp_variants_map = {}
        for record in variants_records:
            # print 'in catalog & in variants', record['rs']
            # tmp_variants_map[record['rs']] = {'genotype':record['genotype']}
            tmp_variants_map[record['rs']] = record['genotype']

        # in catalog, but not in variants
        # null_variant = {'genotype':'na'}
        null_variant = 'na'
        for found_id, catalog in tmp_catalog_map.items():
            rs = catalog['rs']
            if not rs in tmp_variants_map:
                tmp_variants_map[rs] = null_variant


    for found_id, catalog in tmp_catalog_map.items():
        rs = catalog['rs']
        variant = tmp_variants_map[rs]

        if int(found_id) < 10:
            print found_id, rs, catalog.get('trait'), catalog.get('risk_allele'), catalog.get('freq'), catalog.get('OR_or_beta'),
            # print variant['genotype']
            print variant
        elif int(found_id) == 10:
            print 'has more...'

    return tmp_catalog_map, tmp_variants_map

        # only for query_type == rs,
        # not in catalog, but in variants
        #
        # TODO
        #

        # return tmp_catalog_map, tmp_variants_map


def _main():
    parser = argparse.ArgumentParser(description='mongodb query-search for catalog & variants')
    parser.add_argument('-u', '--user_id', required=True)
    parser.add_argument('-v', '--file_name', required=True)
    parser.add_argument('-q', '--query', required=True)
    parser.add_argument('--mongo-port', default=27017)
    args = parser.parse_args()

    catalog_map, variants_map = search_variants(args.user_id, args.file_name, args.query, args.mongo_port)


    for found_id in catalog_map:
        catalog = catalog_map[found_id]
        rs = catalog['rs']
        variant = variants_map[rs]

        print found_id, rs, catalog['trait'], catalog['risk_allele'], catalog['freq'], catalog['OR_or_beta'],
        print variant


if __name__ == '__main__':
    _main()
