import csv

from django.conf import settings

from pergenie.mongo import mongo_db
from lib.gwascatalog import parser, extra
from lib.utils.genome import chr_id2chrom
from lib.utils import clogging
log = clogging.getColorLogger(__name__)

# TODO:
# - Clenup genes


def import_catalog(source, catalog_id):
    catalog = mongo_db['gwascatalog-' + str(catalog_id)]

    # Ensure old collection does not exist
    if catalog.find_one():
        mongo_db.drop_collection(catalog)
    assert catalog.count() == 0

    fields = [('added',                     'Date Added to Catalog',      parser._date),
              ('pubmed_id',                 'PUBMEDID',                   int),
              ('first_author',              'First Author',               str),
              ('date',                      'Date',                       parser._date),
              ('jornal',                    'Journal',                    str),
              ('study',                     'Study',                      parser.str_without_slash),
              ('trait',                     'Disease/Trait',              parser.str_without_slash),
              ('initial_sample_size',       'Initial Sample Size',        str),
              ('replication_sample_size',   'Replication Sample Size',    str),
              ('region',                    'Region',                     str),
              ('chr_id',                    'Chr_id',                     int),
              ('chr_pos',                   'Chr_pos',                    int),
              ('reported_genes',            'Reported Gene(s)',           str),
              ('mapped_genes',              'Mapped_gene',                str),
              ('upstream_gene',             'Upstream_gene_id',           str),
              ('downstream_gene',           'Downstream_gene_id',         str),
              ('snp_genes',                 'Snp_gene_ids',               str),
              ('upstream_gene_distance',    'Upstream_gene_distance',     parser._float),
              ('downstream_gene_distance',  'Downstream_gene_distance',   parser._float),
              ('strongest_snp_risk_allele', 'Strongest SNP-Risk Allele',  str),
              ('snps',                      'SNPs',                       parser.snps),
              ('merged',                    'Merged',                     int),
              ('snp_id_current',            'Snp_id_current',             int),
              ('context',                   'Context',                    str),
              ('intergenc',                 'Intergenic',                 int),
              ('risk_allele_frequency',     'Risk Allele Frequency',      parser._float),
              ('p_value',                   'p-Value',                    str),
              ('p_value_mlog',              'Pvalue_mlog',                parser._float),
              ('p_value_text',              'p-Value (text)',             str),
              ('OR_or_beta',                'OR or beta',                 parser._float),
              ('CI_95',                     '95% CI (text)',              parser.ci_text),
              ('platform',                  'Platform [SNPs passing QC]', parser.platform),
              ('cnv',                       'CNV',                        str)]

    with open(source, 'rb') as fin:
        for i,record in enumerate(csv.DictReader(fin, delimiter='\t')):
            data = {}
            for key, key_orig, converter in fields:
                try:
                    data[key] = _type(converter(record[key_orig].strip()))
                except KeyError:
                    pass

            data['pubmed_link'] = extra.pubmed_link(data['pubmed_id'])
            data['population'] = extra.population(data['initial_sample_size'])
            data['ref'] = extra.reference_allele(data['chr_id'], data['chr_pos'])
            data['OR'] = extra.identfy_or_or_beta(data['OR_or_beta'], data['CI_95'])

            data['risk_snp'], data['risk_allele'] = extra.risk_allele(data)
            data['dbsnp_link'] = extra.dbsnp_link(data['risk_snp'])

            data['rank'] = extra.reliability_rank(data)

            catalog.insert(data)

        log.info('Creating indexes...')
        catalog.create_index('population')
        catalog.create_index('risk_snp')

    log.info('# of documents: {}'.format(catalog.count()))

    # log.info('Validation...')
    # gwascatalog_rsid_map = dict()
    # for x in list(catalog.find()):
    #     if x['chr_id'] and x['chr_pos']:
    #         chr_pos = (chr_id2chrom(x['chr_id']), int(x['chr_pos']))
    #         if chr_pos in gwascatalog_rsid_map:
    #             if gwascatalog_rsid_map[chr_pos] != x['snps']:
    #                 log.warn('Same pos but different rsID: {0}'.format(x))
    #             gwascatalog_rsid_map.update({chr_pos: x['snps']})

    log.info('Done.')
