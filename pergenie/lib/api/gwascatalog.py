import sys, os
import re
import shlex
from pymongo import MongoClient, DESCENDING
from django.conf import settings
from utils import clogging
log = clogging.getColorLogger(__name__)

OR_SYMBOL = '+'


class GWASCatalog(object):
    def __init__(self):
        self.db_select = settings.DB_SELECT['gwascatalog']

    def get_catalog_records(self, rs):
        catalog = self.get_latest_catalog()
        return list(catalog.find({'snps': rs}).sort('date', DESCENDING))

    def get_catalog_record(self, rs):
        catalog = self.get_latest_catalog()
        return catalog.find_one({'snps': rs})

    def search_catalog_by_query(self, raw_query, query_type):
        """
        Search catalog by query.

        Args:

        Returns:

        """

        # parse & build query
        sub_queries = []
        query_map = {'rs': 'snps',
                     'chr': 'chr_id',
                     'population': 'population',
                     'trait': 'trait'}

        if query_type == 'trait':
            sub_queries.append({'trait': raw_query})
        elif query_type == 'population':
            sub_queries.append({'population': re.compile(raw_query)})

        else:
            for query_type, query in self._split_query(raw_query):
                or_queries = []
                log.debug('query: {0}: {1}'.format(query_type, query))
                log.debug(query.split(OR_SYMBOL))

                if query_type == 'gene':
                    for or_sub_query in query.split(OR_SYMBOL):
                        or_queries.append({'reported_genes.gene_symbol': re.compile(or_sub_query, re.IGNORECASE)})
                        or_queries.append({'mapped_genes.gene_symbol': re.compile(or_sub_query, re.IGNORECASE)})

                elif query_type == 'rs' or  query_type == 'chr':  ### complete match only
                    # for or_sub_query in query.split(OR_SYMBOL):
                    #     or_sub_query = int(or_sub_query)
                    #     or_queries.append({query_map[query_type]: re.compile(or_sub_query, re.IGNORECASE)})
                    sub_queries.append({query_map[query_type]: int(query)})

                elif query_type == 'population':
                    # TODO: do not use re.compile, instead, use `X in list`
                    for or_sub_query in query.split(OR_SYMBOL):
                        or_queries.append({'population': re.compile(or_sub_query)})


                elif query_type in query_map:
                    for or_sub_query in query.split(OR_SYMBOL):
                        or_queries.append({query_map[query_type]: re.compile(or_sub_query, re.IGNORECASE)})

                else:
                    for or_sub_query in query.split(OR_SYMBOL):
                        or_queries.append({'trait': re.compile(or_sub_query, re.IGNORECASE)})

                if or_queries:
                    sub_queries.append({'$or': or_queries})

        # query search
        catalog = self.get_latest_catalog()
        query = {'$and': sub_queries}
        log.debug(query)
        catalog_records = catalog.find(query)  # .sort('snps', 1)

        return catalog_records

    def _split_query(self, raw_query):
        """Classify raw_query into rs, trait, ...etc.
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

    def get_latest_catalog(self):
        if self.db_select == 'mongodb':
            with MongoClient(host=settings.MONGO_URI) as c:
                latest_document = c['pergenie']['catalog_info'].find_one({'status': 'latest'})  # -> {'date': datetime.datetime(2012, 12, 12, 0, 0),}

                if latest_document:
                    latest_date = str(latest_document['date'].date()).replace('-', '_')  # -> '2012_12_12'
                    catalog = c['pergenie']['catalog'][latest_date]
                else:
                    log.error('latest does not exist in catalog_info!')

        return catalog

    def get_latest_catalog_date(self):
        if self.db_select == 'mongodb':
            with MongoClient(host=settings.MONGO_URI) as c:
                catalog_info = c['pergenie']['catalog_info']
                latest_catalog_date = catalog_info.find_one({'status': 'latest'})['date']

        return latest_catalog_date

    def get_latest_added_date(self):
        if self.db_select == 'mongodb':
            with MongoClient(host=settings.MONGO_URI) as c:
                catalog_stats = c['pergenie']['catalog_stats']

                # NOTE: If catalog is under importing, this date may not be correct. But it's ok.
                latest_datetime = list(catalog_stats.find({'field': 'added'}).sort('value', DESCENDING))[0]['value']
                latest_date = latest_datetime.date()

        return latest_date

    def get_recent_catalog_records(self):
        if self.db_select == 'mongodb':
            with MongoClient(host=settings.MONGO_URI) as c:
                catalog = self.get_latest_catalog()
                recent_date = list(catalog.find().sort('added', DESCENDING))[0]['added']
                recent_records = list(catalog.find({'added': recent_date}))

                uniq_studies, uniq_ids = list(), set()
                for record in recent_records:
                    if not record['pubmed_id'] in uniq_ids:
                        uniq_studies.append(record)
                        uniq_ids.update([record['pubmed_id']])

                        # limit to 3 studies
                        if len(uniq_ids) == 3:
                            break

        return uniq_studies

    # TODO: need to merge
    def get_traits_infos(self):
        if self.db_select == 'mongodb':
            with MongoClient(host=settings.MONGO_URI) as c:
                trait_info = c['pergenie']['trait_info']

                founds = trait_info.find({})
                traits = set([found['eng'] for found in founds])
                traits_ja = [trait_info.find_one({'eng': trait})['ja'] for trait in traits]
                traits_category = [trait_info.find_one({'eng': trait})['category'] for trait in traits]
        return traits, traits_ja, traits_category

    def get_uniq_snps_list(self):
        if self.db_select == 'mongodb':
            with MongoClient(host=settings.MONGO_URI) as c:
                catalog_stats = c['pergenie']['catalog_stats']
        return sorted(list(set([rec['value'] for rec in list(catalog_stats.find({'field': 'snps'}))])))
