#!/usr/bin/env python2.7
# -*- coding: utf-8 -*- 

import argparse
import re
import shlex
import pymongo


def _split_query(raw_query):
    """
    Classify raw_query into rs, trait, ...etc.
    """

    for query in shlex.split(raw_query):
        try:
            if re.match('rs[0-9]+', query):
                yield 'rs', int(re.match('rs([0-9]+)', query).group(1))
            elif re.match('gene:', query):
                yield 'gene', re.match('gene:(\S+)', query).group(1)
            elif re.match('chr:', query):
                yield 'chr', int(re.match('chr:(\S+)', query).group(1))
            elif re.match('population:', query):
                yield 'population', re.match('population:(\S+)', query).group(1)
            elif re.match('trait:', query):
                yield 'trait', re.match('trait:(\S+)', query).group(1)
            else:
                yield 'trait', query
        except AttributeError: # except blank query. ex.) gene:
            yield '', ''


def search_catalog_by_query(raw_query):

    # parse & build query
    sub_queries = []
    for query_type, query in _split_query(raw_query):
        print 'query: {0}: {1}'.format(query_type, query)
        if query_type == 'rs':
            sub_queries.append({'snps': query})
        elif query_type == 'gene':
            sub_queries.append({'reported_genes.gene_symbol' : re.compile(query, re.IGNORECASE)})
            sub_queries.append({'mapped_genes.gene_symbol' : re.compile(query, re.IGNORECASE)})
        elif query_type == 'chr':
            sub_queries.append({'chr_id' : query})
        elif query_type == 'population':
            sub_queries.append({'initial_sample_size': re.compile(query, re.IGNORECASE)})
        else:
            sub_queries.append({'trait': re.compile(query, re.IGNORECASE)})

    with pymongo.Connection() as connection:
        db = connection['pergenie']
        catalog = db['catalog']

        query = {'$and': sub_queries}
        catalog_records = catalog.find(query)# .sort('snps', 1)

        return catalog_records


def _main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('query')
    args = arg_parser.parse_args()

    found_records = search_catalog_by_query(args.query)

    for record in found_records.sort('trait', 1):
        print record['snps'], record['trait'], record['risk_allele'], record['risk_allele_frequency'], record['OR_or_beta']

if __name__ == '__main__':
    _main()
