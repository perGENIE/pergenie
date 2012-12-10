#!/usr/bin/env python2.7
# -*- coding: utf-8 -*- 

import argparse
import re
import shlex
import pymongo

OR_SYMBOL = '+'

def _split_query(raw_query):
    """
    Classify raw_query into rs, trait, ...etc.
    """

    for query in shlex.split(raw_query):
        try:
            if re.match('rs[0-9]+', query):
                yield 'rs', re.match('rs([0-9]+)', query).group(1)
            elif re.match('gene:', query):
                yield 'gene', re.match('gene:(\S+)', query).group(1)
            elif re.match('chr:', query):
                yield 'chr', re.match('chr:(\S+)', query).group(1)
            elif re.match('population:', query):
                yield 'population', re.match('population:(\S+)', query).group(1)
            elif re.match('trait:', query):
                yield 'trait', re.match('trait:(\S+)', query).group(1)
            else:
                yield 'trait', query
        except AttributeError: # except blank query. ex.) gene:
            yield '', ''


def search_catalog_by_query(raw_query, query_type=None, mongo_port=27017):

    # parse & build query
    sub_queries = []
    query_map = {'rs': 'snps',
                 'chr': 'chr_id',
                 'population': 'initial_sample_size',
                 'trait': 'trait'}

                 # 'gene': ['mapped_genes.gene_symbol', 'reported_genes.gene_symbol']

    if query_type == 'trait':
        sub_queries.append({'trait': raw_query})

    else:
        for query_type, query in _split_query(raw_query):
            or_queries = []
            print 'query: {0}: {1}'.format(query_type, query)
            print query.split(OR_SYMBOL)

            if query_type == 'gene':
                for or_sub_query in query.split(OR_SYMBOL):
                    or_queries.append({'reported_genes.gene_symbol': re.compile(or_sub_query, re.IGNORECASE)})
                    or_queries.append({'mapped_genes.gene_symbol': re.compile(or_sub_query, re.IGNORECASE)})

            elif query_type == 'rs' or  query_type == 'chr':  ### complete match only
                # for or_sub_query in query.split(OR_SYMBOL):
                #     or_sub_query = int(or_sub_query)
                #     or_queries.append({query_map[query_type]: re.compile(or_sub_query, re.IGNORECASE)})
                sub_queries.append({query_map[query_type]: int(query)})

            elif query_type in query_map:
                for or_sub_query in query.split(OR_SYMBOL):
                    or_queries.append({query_map[query_type]: re.compile(or_sub_query, re.IGNORECASE)})

            else:
                for or_sub_query in query.split(OR_SYMBOL):
                    or_queries.append({'trait': re.compile(or_sub_query, re.IGNORECASE)})

            if or_queries:
                sub_queries.append({'$or': or_queries})
    

    with pymongo.Connection(port=mongo_port) as connection:
        db = connection['pergenie']
        catalog = db['catalog']
        query = {'$and': sub_queries}
        print query
        catalog_records = catalog.find(query)# .sort('snps', 1)

        return catalog_records


def _main():
    parser = argparse.ArgumentParser()
    parser.add_argument('query')
    parser.add_argument('--type')
    parser.add_argument('--mongo-port', default=27017)
    args = parser.parse_args()

    found_records = search_catalog_by_query(args.query, query_type=args.type, mongo_port=args.mongo_port)

    for record in found_records.sort('trait', 1):
        print record['snps'], record['trait'], record['risk_allele'], record['risk_allele_frequency'], record['OR_or_beta'], record['initial_sample_size']

if __name__ == '__main__':
    _main()
