# -*- coding: utf-8 -*-

import sys, os
import re
import csv
import datetime
import time
import json
# from collections import Counter  # py27
from utils.Counter import Counter  # py26 (//code.activestate.com/recipes/576611/)
from pprint import pformat
import pymongo
import HTMLParser
h = HTMLParser.HTMLParser()
from xml.sax.saxutils import *

from extract_region import extract_region
from get_reference_seq import MyFasta
from lib.mysql.bioq import Bioq

from utils import clogging
log = clogging.getColorLogger(__name__)

_g_gene_symbol_map = {}  # { Gene Symbol => (Entrez Gene ID, OMIM Gene ID) }
_g_gene_id_map = {}      # { Entrez Gene ID => (Gene Symbol, OMIM Gene ID) }

REVERSED_STATS = {'GMAF': 0, 'RV': 0}

def import_catalog(path_to_gwascatalog, settings):
    path_to_mim2gene = settings.PATH_TO_MIM2GENE
    path_to_eng2ja = settings.PATH_TO_ENG2JA
    path_to_disease2wiki = settings.PATH_TO_DISEASE2WIKI
    path_to_interval_list_dir = settings.PATH_TO_INTERVAL_LIST_DIR
    path_to_reference_fasta = settings.PATH_TO_REFERENCE_FASTA
    dbsnp_version = settings.DBSNP_VERSION
    mongo_port = settings.MONGO_PORT

    c = pymongo.MongoClient(port=mongo_port)
    bq = Bioq(settings.DATABASES['bioq']['HOST'],
              settings.DATABASES['bioq']['USER'],
              settings.DATABASES['bioq']['PASSWORD'],
              settings.DATABASES['bioq']['NAME'])

    with open(path_to_mim2gene, 'rb') as fin:
        for record in csv.DictReader(fin, delimiter='\t'):
            gene_type = record['Type'].lower()
            if gene_type.find('gene') < 0: continue

            omim_gene_id = record['# Mim Number']
            entrez_gene_id = record['Gene IDs']
            gene_symbol = record['Approved Gene Symbols']

            _g_gene_symbol_map[gene_symbol] = entrez_gene_id, omim_gene_id
            _g_gene_id_map[entrez_gene_id] = gene_symbol, omim_gene_id

            # _g_gene_id_map =
            # {'7015': ('TERT', '187270'), ...}
    # TODO: Add database for `entrez_gene_id to gene_symbol`

    disease2wiki = json.load(open(path_to_disease2wiki))

    # Create db for eng2ja, eng2category, ...
    trait_info = c['pergenie']['trait_info']

    if trait_info.find_one():
        c['pergenie'].drop_collection(trait_info)
    assert trait_info.count() == 0

    # TODO: remove eng2ja, then use only db.trait_info
    log.debug('Loading {0} ...'.format(path_to_eng2ja))
    eng2ja = {}
    eng2category = {}
    with open(path_to_eng2ja, 'rb') as fin:
        for record in csv.DictReader(fin, delimiter='\t'):
            if not record['eng'] == '#':  # ignore `#`
                # TODO: remove eng2ja & eng2category
                eng2ja[record['eng']] = unicode(record['ja'], 'utf-8') or record['eng']
                eng2category[record['eng']] = record['category'] or 'NA'

                #
                ja = unicode(record['ja'], 'utf-8') or record['eng']
                category = record['category'] or 'NA'
                is_drug_response = record['is_drug_response'] or 'NA'
                wiki_url_en = disease2wiki.get(record['eng'], '')

                clean_record = dict(eng=record['eng'], ja=ja,
                                    category=category,
                                    is_drug_response=is_drug_response,
                                    wiki_url_en=wiki_url_en)

                trait_info.insert(clean_record, upsert=True)  # insert if not exist

        trait_info.ensure_index('eng', unique=True)

    # ==============
    # Import catalog
    # ==============

    catalog_date_raw = os.path.basename(path_to_gwascatalog).split('.')[1]
    # catalog_date = datetime.datetime.strptime(catalog_date_raw , '%Y_%m_%d')

    catalog = c['pergenie']['catalog'][catalog_date_raw]
    catalog_stats = c['pergenie']['catalog_stats']
    catalog_cover_rate = c['pergenie']['catalog_cover_rate']
    counter = Counter()

    # ensure old collections does not exist
    if catalog.find_one(): c['pergenie'].drop_collection(catalog)
    assert catalog.count() == 0
    if catalog_stats.find_one(): c['pergenie'].drop_collection(catalog_stats)
    assert catalog_stats.count() == 0
    if catalog_cover_rate.find_one(): c['pergenie'].drop_collection(catalog_cover_rate)
    assert catalog_cover_rate.count() == 0

    strand_db = c['strand_db']
    if not strand_db.collection_names():
        log.warn('========================================')
        log.warn('strand_db does not exist in mongodb ...')
        log.warn('so strand check will be skipped')
        log.warn('========================================')
        strand_db = None

    dbsnp = c['dbsnp'][dbsnp_version]
    if not dbsnp.find_one():
        log.warn('========================================')
        log.warn('dbsnp.{0} does not exist in mongodb ...'.format(dbsnp_version))
        log.warn('so dbSNP check will be skipped')
        log.warn('========================================')
        dbsnp = None

    if path_to_reference_fasta:
        fa = MyFasta(path_to_reference_fasta)
    else:
        log.warn('========================================')
        log.warn('Reference Genome FASTA does not exist...')
        log.warn('so `ref` for rs will not be added')
        log.warn('========================================')
        fa = None

    my_fields = [('my_added', 'Date Added to MyCatalog', _date),
                 ('who_added', 'Who Added', _string),
                 ('activated', 'Activated', _integer),
                 ('population', 'Population', _string),
                 ('DTC', 'DTC genetic testing companies', _string),
                 ('clinical', 'Clinical Channel', _string)]

    fields = [('added', 'Date Added to Catalog', _date),
              ('pubmed_id', 'PUBMEDID', _integer),
              ('first_author', 'First Author', _string),
              ('date', 'Date', _date),
              ('jornal', 'Journal', _string),
              ('study', 'Study', _string_without_slash),
              ('trait', 'Disease/Trait', _string_without_slash),
              ('initial_sample_size', 'Initial Sample Size', _string),
              ('replication_sample_size', 'Replication Sample Size', _string),
              ('region', 'Region', _string),
              ('chr_id', 'Chr_id', _integer),
              ('chr_pos', 'Chr_pos', _integer),
              ('reported_genes', 'Reported Gene(s)', _genes_from_symbols),
              ('mapped_genes', 'Mapped_gene', _genes_from_symbols),
              ('upstream_gene', 'Upstream_gene_id', _gene_from_id),
              ('downstream_gene', 'Downstream_gene_id', _gene_from_id),
              ('snp_genes', 'Snp_gene_ids', _genes_from_ids),
              ('upstream_gene_distance', 'Upstream_gene_distance', _float),
              ('downstream_gene_distance', 'Downstream_gene_distance', _float),
              ('strongest_snp_risk_allele', 'Strongest SNP-Risk Allele', _string),
              ('snps', 'SNPs', _rss),
              ('merged', 'Merged', _integer),
              ('snp_id_current', 'Snp_id_current', _integer),
              ('context', 'Context', _string),
              ('intergenc', 'Intergenic', _integer),
              ('risk_allele_frequency', 'Risk Allele Frequency', _float),
              ('p_value', 'p-Value', _p_value),
              ('p_value_mlog', 'Pvalue_mlog', _float),
              ('p_value_text', 'p-Value (text)', _string),
              ('OR_or_beta', 'OR or beta', _OR_or_beta),
              ('CI_95', '95% CI (text)', _CI_text),
              ('platform', 'Platform [SNPs passing QC]', _string),
              ('cnv', 'CNV', _string)]

    post_fields = [('risk_allele', 'Risk Allele'),
                   ('eng2ja', 'Disease/Trait (in Japanese)'),
                   ('OR', 'OR')]

    field_names = [field[0:2] for field in fields] + post_fields

    fields = my_fields + fields
    log.info('# of fields: {0}'.format(len(fields)))

    log.debug('Importing gwascatalog.txt...')
    with open(path_to_gwascatalog, 'rb') as fin:
        for i,record in enumerate(csv.DictReader(fin, delimiter='\t')):  # , quotechar="'"):
            # some traits contains `spaces` at the end of it, e.g., "Airflow obstruction "...
            record['Disease/Trait'] = record['Disease/Trait'].rstrip()

            data = {}
            for dict_name, record_name, converter in fields:
                try:
                    data[dict_name] = converter(record[record_name])
                except KeyError:
                    pass

            data['eng2ja'] = eng2ja.get(data['trait'])
            data['pubmed_link'] = 'http://www.ncbi.nlm.nih.gov/pubmed/' + str(data['pubmed_id'])
            data['dbsnp_link'] = 'http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=' + str(data['snps'])
            data['is_in_truseq'] = False
            data['is_in_andme'] = False
            data['population'] = _population(data['initial_sample_size'])

            if data['chr_id'] and data['chr_pos']:
                data['ref'] = fa.get_seq({23: 'X', 24: 'Y', 25: 'M'}.get(data['chr_id'], data['chr_id']), data['chr_pos'], 1)
            else:
                data['ref'] = ''

            if (not data['snps']) or (not data['strongest_snp_risk_allele']):
                log.warn('absence of "snps" or "strongest_snp_risk_allele" {0} {1}. pubmed_id:{2}'.format(data['snps'], data['strongest_snp_risk_allele'], data['pubmed_id']))
                data['snps'], data['strongest_snp_risk_allele'], data['risk_allele'] = 'na', 'na', 'na'
                catalog.insert(data)
                continue

            rs, data['risk_allele'] = _risk_allele(data, dbsnp=dbsnp, strand_db=strand_db)
            if data['snps'] != rs:
                log.warn('"snps" != "risk_allele": {0} != {1}'.format(data['snps'], rs))
                catalog.insert(data)
                continue

            # identfy OR or beta & TODO: convert beta to OR if can
            data['OR'] = identfy_OR_or_beta(data['OR_or_beta'], data['CI_95'])

            # for DEGUG
            if type(data['OR']) == float:
                data['OR_or_beta'] = data['OR']
            else:
                data['OR_or_beta'] = None

            # TODO: support gene records
            for field,value in data.items():
                if '_gene' in field or field == 'CI_95':
                    pass
                else:
                    if type(value) == list:
                        value = str(value)
                    counter[(field, value)] += 1

            # TODO: call `add_record_reliability`
            # add_record_reliability(data)

            catalog.insert(data)

        counter_dicts = [{'field':k[0], 'value':k[1], 'count':v} for (k,v) in dict(counter).items()]
        catalog_stats.insert(counter_dicts)

        log.info('Creating indexes...')
        catalog.create_index('population')
        catalog_stats.create_index('field')

    log.info('# of documents in catalog (after): {0}'.format(catalog.count()))
    log.info('REVERSED_STATS: {0}'.format(pformat(REVERSED_STATS)))

    # Add `is_in_truseq`, `is_in_andme` flags
    n_records, n_truseq, n_andme = 0, 0, 0
    for chrom in [i + 1 for i in range(24)]:
        log.info('Addding flags... chrom: {0}'.format(chrom))

        # TODO: should be `uniq_` ?
        records = list(catalog.find({'chr_id': chrom}).sort('chr_pos', pymongo.ASCENDING))

        ok_records = [rec for rec in records if rec['snp_id_current']]
        n_records += len(ok_records)
        log.info('records:{0}'.format(n_records))

        # `is_in_truseq`
        region_file = os.path.join(path_to_interval_list_dir,
                                   'TruSeq-Exome-Targeted-Regions-BED-file.{0}.interval_list'.format({23:'X', 24:'Y'}.get(chrom, chrom)))
        with open(region_file, 'r') as fin:
            extracted = extract_region(region_file, ok_records)
            n_truseq += len(extracted)
            log.info('`is_in_truseq` extracted:{0}'.format(n_truseq))
            for record in extracted:
                catalog.update(record, {"$set": {'is_in_truseq': True}})

        # `is_in_andme`
        region_file = os.path.join(path_to_interval_list_dir,
                                   'andme_region.{0}.interval_list'.format({23:'X', 24:'Y', 25:'MT'}.get(chrom, chrom)))
        with open(region_file, 'r') as fin:
            extracted = extract_region(region_file, ok_records)
            n_andme += len(extracted)
            log.info('`is_in_andme` extracted:{0}'.format(n_andme))
            for record in extracted:
                catalog.update(record, {"$set": {'is_in_andme': True}})

    len_genome = 2861327131  # number of bases (exclude `N`)
    len_truseq = 62085286
    len_andme = 1022124
    stats = [{'stats': 'catalog_cover_rate',
              'values': {'vcf_whole_genome': 100,
                         'vcf_exome_truseq': int(round(100 * n_truseq / n_records)),
                         'andme': int(round(100 * n_andme / n_records))}},
             {'stats': 'genome_cover_rate',
              'values': {'vcf_whole_genome': 100,
                         'vcf_exome_truseq': int(round(100 * len_truseq / len_genome)),
                         'andme': int(round(100 * len_andme / len_genome))}}
             ]

    log.info(stats)
    catalog_cover_rate.insert(stats)

    log.info('catalog.find_one(): {0}'.format(catalog.find_one()))
    log.info('import catalog done')

    return


# def add_record_reliability(data):
#     """Add record reliability.

#     To prioritize GWAS Catalog's records, like Meta-GWAS > GWAS,
#     calculate 'record_reliability' from 'study', 'initial_sample_size', ...
#     then add 'record_reliability' to `data`.

#     Arg:
#     data: a GWAS Catalog's record (dict), to be inserted to MongoDB.
#           data = {'study': '...',
#                   'initial_sample_size': '...', ...}

#     RetVal:
#     None
#     """


def _population(text):
    """
    Parse `initial_sample_size` in GWAS Catalog,
    then return a list of combination of
    'European', 'Asian', 'African', 'Japanese', e.g.:

    ['African', 'Asian', 'European']

    If undefined or uncategorized, returns:

    ['']
    """
    result = set()

    # TODO: research about `human classification`

    # ? Hispanic
    # ? Mexican-American
    # ? Hispanic/Latin American

    # ? Native American
    # ? Indo-European  # Celts?

    # ? Hutterite
    # ? South African Afrikaner

    # ? Australian

    regexps = [(re.compile(' European ((|ancestry|descent)|(|individual(|s)))', re.I), 'European'),
               (re.compile('European American', re.I), 'European'),
               (re.compile('Caucasian', re.I), 'European'),
               (re.compile('white', re.I), 'European'),
               (re.compile(' EA '), 'European'),
               (re.compile('Australian', re.I), 'European'),
               (re.compile('UK', re.I), 'European'),
               (re.compile('British', re.I), 'European'),
               (re.compile('Framingham', re.I), 'European'),
               (re.compile('Amish', re.I), 'European'),
               (re.compile('Ashkenazi Jewish', re.I), 'European'),
               (re.compile('French', re.I), 'European'),
               (re.compile('Italian', re.I), 'European'),
               (re.compile('German', re.I), 'European'),
               (re.compile('Croatian', re.I), 'European'),
               (re.compile('Scottish', re.I), 'European'),
               (re.compile('Icelandic', re.I), 'European'),
               (re.compile('Romanian', re.I), 'European'),
               (re.compile('Dutch', re.I), 'European'),
               (re.compile('Danish', re.I), 'European'),
               (re.compile('Swedish', re.I), 'European'),
               (re.compile('Scandinavian', re.I), 'European'),
               (re.compile('Finnish', re.I), 'European'),
               (re.compile('Sardinian', re.I), 'European'),
               (re.compile('Swiss', re.I), 'European'),
               (re.compile('Sorbian', re.I), 'European'),

               (re.compile('Turkish', re.I), 'European'),
               (re.compile('Hispanic ancestry', re.I), 'European'),
               (re.compile('Hispanic\/', re.I), 'European'),
               (re.compile('Mexican( |-)American(|s)', re.I), 'European'),
               (re.compile('Indo-European', re.I), 'European'),

               (re.compile('[^South] African ((|ancestry|descent)|(|individual(|s)))', re.I), 'African'),
               (re.compile('[^South] African(|-) American', re.I), 'African'),
               (re.compile('Malawian', re.I), 'African'),

               (re.compile('(|East|South|Indian|Southeast) Asian', re.I), 'Asian'),
               (re.compile('Korean', re.I), 'Asian'),
               (re.compile('Taiwanese', re.I), 'Asian'),
               (re.compile('Indonesian', re.I), 'Asian'),
               (re.compile('Micronesian', re.I), 'Asian'),
               (re.compile('Han Chinese', re.I), 'Asian'),
               (re.compile('Chinese Han', re.I), 'Asian'),
               (re.compile('Southern Chinese', re.I), 'Asian'),
               (re.compile('Indian', re.I), 'Asian'),
               (re.compile('Malay', re.I), 'Asian'),
               (re.compile(' Chinese', re.I), 'Asian'),
               (re.compile('Thai-Chinese', re.I), 'Asian'),
               (re.compile('Filipino', re.I), 'Asian'),
               (re.compile('Vietnamese', re.I), 'Asian'),
               (re.compile('Japanese', re.I), 'Asian'),

               (re.compile('Japanese', re.I), 'Japanese'),
           ]

    for regexp, population in regexps:
        founds = regexp.findall(text)

        if founds:
            result.update([population])

    return sorted(list(result))


def identfy_OR_or_beta(OR_or_beta, CI_95):
    if CI_95['text']:
        # TODO: convert beta to OR if can
        OR = 'beta:{0}'.format(OR_or_beta)

    else:
        if OR_or_beta:
            OR = float(OR_or_beta)

            #
            if OR < 1.0:  # somehow beta without text in 95% CI ?
                OR = 'beta:{0}?'.format(OR_or_beta)

        else:
            OR = None

    return OR


def _CI_text(text):
    """
    * 95% Confident interval

      * if is beta coeff., there is text. elif OR, no text.
    """
    result = {}

    if not text or text in ('NR', 'NS'):  # nothing or NR or NS
        result['CI'] = None
        result['text'] = None

    else:
        re_CI_text = re.compile('\[(.+)\](.*)')
        texts = re_CI_text.findall(text)

        if not len(texts) == 1:  # only text
            result['CI'] = None
            re_CInone_text = re.compile('(.*)')
            texts = re_CInone_text.findall(text)
            assert len(text[0]) == 1, '{0} {1}'.format(text, texts)
            result['text']  = texts[0][0]

        else:
            assert len(texts[0]) == 2, '{0} {1}'.format(text, texts)  # [] & text

            #
            if ']' in texts[0][0]:  # [] ] somehow there is ] at end... like [0.006-0.01] ml/min/1.73 m2 decrease]
                retry_re_CI_text = re.compile('\[(.+)\](.*)\]')
                texts = retry_re_CI_text.findall(text)

            if texts[0][0] in ('NR', 'NS'):
                result['CI'] = None
            else:
                CIs = re.split('(, | - |- | -| |-|)', str(texts[0][0]))

                try:
                    if not len(CIs) == 3:
                        log.warn('{0} {1} {2}'.format(text, texts[0][0], CIs))
                        if CIs[0] == '' and CIs[1] == '-' and CIs[3] == '-':  # [-2.13040-19.39040]
                            result['CI'] = [(-1) * float(CIs[2]), float(CIs[4])]
                        else:
                            log.warn('{0} {1}'.format(text, texts))
                            time.sleep(2)
                    else:
                        result['CI'] = [float(CIs[0]), float(CIs[2])]

                except ValueError:
                    #
                    if CIs[2] == '.5.00':
                        CIs[2] = float(5.00)
                        result['CI'] = [float(CIs[0]), float(CIs[2])]
                    #
                    elif texts[0][0] == 'mg/dl decrease':
                        result['CI'] = None
                        result['text'] = 'mg/dl decrease'
                        return result

            if texts[0][1]:  # beta coeff.
                result['text']  = texts[0][1].lstrip()
            else:  # OR
                result['text'] = None

    return result


def _OR_or_beta(text):
    """
    * parse odds-ratio or beta-coeff.

      * in GWAS Catalog, OR>1 is asserted.
      * OR and beta are mixed. (to identify, we need to check 95% CI text)
    """

    if not text or text in ('NR', 'NS'):
        return None
    else:
        try:
            value = float(text)
        except ValueError:
            match = re.match('\d*\.\d+', text)
            if match:
                value = float(match.group())
            else:
                log.warn('OR_or_beta? {0}'.format(text))
                return None

        return value
        # if value >= 1.0:
        #     return value

        # else:
        #     print >>sys.stderr, 'OR_or_beta? {0}'.format(text)
        #     return text+'?'


def _rss(text):
    """
    TODO: support multiple rss records. (temporary, if multiple rss, rss = None)
    """

    if not text or text in ('NR', 'NS'):
        return None

    else:
        if len(text.split(',')) != 1:
            log.warn('in _rss, more than one rs: {0}'.format(text))
            return None   #

        try:
            return int(text.replace('rs', ''))
        except ValueError:
            log.warn('in _rss, failed to convert to int: {0}'.format(text))
            return None   #

def _platform(text):
    """

    >>> _platform('Illumina [2,272,849] (imputed)')
    ['Illumina']
    >>> _platform('Ilumina [475,157]')
    ['Illumina']
    >>> _platform('Affymetrix & Illumina [2,217,510] (imputed)')
    ['Affymetrix', 'Illumina']
    >>> _platform('Affymetrix[200,220]')
    ['Affymetrix']
    >>> _platform('Afymetrix [287,554]')
    ['Affymetrix']
    >>> _platform('Perlegen[438,784]')
    ['Perlegen']

    """
    if not text: return []

    result = set()
    regexps = [(re.compile('Il(|l)umina', re.I), 'Illumina'),
               (re.compile('Af(|f)ymetrix', re.I), 'Affymetrix'),
               (re.compile('Perlegen', re.I), 'Perlegen')]

    for regexp, vender in regexps:
        founds = regexp.findall(text)

        if founds: result.update([vender])

    return sorted(list(result))

def _risk_allele(data, dbsnp=None, strand_db=None):
    """Use strongest_snp_risk_allele in GWAS Catalog as risk allele, e.g., rs331615-T -> T

    Following checks will be done if available.

    * Strand check: If strand of snp is `-` in strand_db, convert it to reverse complement,
                    so that all the snp are in `+` oriented.

    * dbSNP check:

    TODO:

    * Consistency check based on allele frequency.

    """
    # Parse `strongest_snp_risk_allele`
    if not data['strongest_snp_risk_allele']:
        return None, None

    regexp_risk_allele = re.compile('rs(\d+)\-(\S+)')
    try:
        rs, risk_allele = regexp_risk_allele.findall(data['strongest_snp_risk_allele'])[0]
    except (ValueError, IndexError):
        log.warn('failed to parse "strongest_snp_risk_allele": {0}'.format(data))
        return None, None

    if risk_allele == '?':
        return int(rs), risk_allele

    if not risk_allele in ('A', 'T', 'G', 'C'):
        log.warn('allele is not in (A,T,G,C): {0}'.format(data))
        return int(rs), None

    # Strand checks
    RV = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}
    chrom = data['chr_id']
    pos = data['chr_pos']
    population = data['population']
    platform = _platform(data['platform'])
    rs = int(rs)

    # if strand_db:
    #     if platform:
    #         for vender in platform:
    #             print chrom, pos
    #             strand_record  = strand_db[vender].find_one({'chrom': chrom, 'pos': pos})
    #             log.debug(strand_record)

    #             # For Affymetrix, retry with rsid.
    #             if vender == 'Affymetrix' and not strand_record:
    #                 strand_record  = strand_db[vender].find_one({'rs': rs})

    #             if strand_record:
    #                 log.info('in strand_db {0}'.format(strand_record))
    #                 if strand_record['strand'] == '-':
    #                     log.warn('RVed allele {0}'.format(data))
    #                     risk_allele = RV[risk_allele]

    if dbsnp:
        dbsnp_vcf = dbsnp.find_one({'rs': rs})
        snp_summary = bq.get_snp_summary(rs)
        ref = bq_snp_summary['ancestral_alleles']
        allele_freqs, _ = bq.get_allele_freqs(rs)

        if not snp_summary:
            log.warn('rs{0} is not in dbSNP ...'.format(rs))
            return int(rs), risk_allele + '?'

        # Get maf & minor allele
        # TODO: what sholud we do, when allele freq is not available ?
        m_freq = 1.0
        m_allele = ''
        for allele, freq in allele_freqs[population].items():
            if freq['freq'] < m_freq:
                m_freq =  freq['freq']
                m_allele = allele

        # # Get GMAF
        # gmaf = dbsnp_vcf('info')

        # Get RV?

        # check rs [964184, 10762058, 9319321]

        if m_allele:
            if data['risk_allele_frequency'] <= 0.5 and m_freq <= 0.5:

            # if not gmaf <= 0.5:
            #     log.debug('GMAF > 0.5...')

            # Suspicious case
            # ref_freq = 1.0 - gmaf
            # if ref == risk_allele and alt == RV[risk_allele]:
                # if ref_freq > 0.5 and data['risk_allele_frequency'] <= 0.5:
                #     log.warn('=======================================================')
                #     log.warn('Suspicious case in Allele frequency check, based on GMAF.')
                #     log.warn('risk_allele_frequency is not consistent with GMAF.')
                #     log.warn('Maybe risk_allele is reverse stranded, so reverse it.')
                #     log.warn(data)
                #     log.warn('=======================================================')
                #     REVERSED_STATS['GMAF'] += 1
                #     return int(rs), RV[risk_allele]
                pass


        # Strand check based on `RV` tag.
        if is_RV:
            log.debug('is RV...')

            # Suspicious case
            if not risk_allele in [ref] + alts:
                if RV[risk_allele] in [ref] + alts:
                    log.warn('=================================================================')
                    log.warn('Suspicious case in Allele frequency check, based RV tag.')
                    log.warn('risk_allele is not in ref + alts, but RV[risk_allele] is in them.')
                    log.warn('Maybe risk_allele is reverse stranded, so reverse it.')
                    log.warn(data)
                    log.warn('=================================================================')
                    REVERSED_STATS['RV'] += 1
                    return int(rs), RV[risk_allele]

    return int(rs), risk_allele


def _p_value(text):
    if not text or text in ('NR', 'NS'):
        return None
    else:
        return text


def _integer(text):
    if not text or text in ('NR', 'NS'):
        return None
    else:
        return int(text)


def _float(text):
    if not text or text in ('NR', 'NS'):
        return None
    else:
        try:
            return float(text)

        except ValueError:
#             msg = '[WARNING] Failed to convert to float, Text: {0}'
#             print >>sys.stderr, msg.format(text)

            match = re.match('\d*\.\d+', text)
            if match:
                return float(match.group())
            else:
                return None


def _string(text):
    if not text or text in ('NR', 'NS'):
        return None
    else:
        return text


def _string_without_slash(text):
    if not text or text in ('NR', 'NS'):
        return None
    else:
        if escape(text) != text:
            log.warn('Escaped: {0}'.format(text))

        # HTML Escape
        text = escape(text)

        # if h.unescape(text) != text:
        #     log.error('Problem with escaping: {0}'.format(text))
        # elif unescape(text) != text:
        #     log.error('Problem with escaping: {0}'.format(text))

        # Escape slash
        if '/' in text:
            log.warn('/ in {0}'.format(text))
        text = text.replace('/', '&#47;')

        return text


def _date(text):
    if not text:
        return None
    else:
        return datetime.datetime.strptime(text, '%m/%d/%Y')


def _gene(gene_symbol, entrez_gene_id, omim_gene_id):
    return {'gene_symbol': gene_symbol,
            'entrez_gene_id': entrez_gene_id,
            'omim_gene_id': omim_gene_id}


def _genes_from_symbols(text):
    if not text or text in ('NR', 'NS', 'Intergenic'):
        return []

    else:
        result = []

        for gene_symbol in re.split('(,|;| - | )', text):
            gene_symbol = gene_symbol.strip()
            if not gene_symbol or gene_symbol in (',', ';', '-'): continue

            if gene_symbol in _g_gene_symbol_map:
                entrez_gene_id, omim_gene_id = _g_gene_symbol_map[gene_symbol]
                result.append(_gene(gene_symbol, entrez_gene_id, omim_gene_id))

            else:
#                 msg = '[WARNING] Failed to find gene from mim2gene, GeneSymbol: {0}'
#                 print >>sys.stderr, msg.format(gene_symbol)

                result.append(_gene(gene_symbol, None, None))

        return result


def _gene_from_id(text):
    if not text or text in ('NR', 'NS'):
        return None

    else:
        entrez_gene_id = int(text)

        if entrez_gene_id in _g_gene_id_map:
            gene_symbol, omim_gene_id = _g_gene_id_map[entrez_gene_id]
            return _gene(gene_symbol, entrez_gene_id, omim_gene_id)

        else:
#             msg = '[WARNING] Failed to find gene from mim2gene, EntrezGeneID: {0}'
#             print >>sys.stderr, msg.format(entrez_gene_id)

            return _gene(None, entrez_gene_id, None)


def _genes_from_ids(text):
    if not text or text in ('NR', 'NS'):
        return None

    else:
        result = []

        for entrez_gene_id in map(int, text.split(';')):
            if str(entrez_gene_id) in _g_gene_id_map:
                gene_symbol, omim_gene_id = _g_gene_id_map[entrez_gene_id]
                result.append(_gene(gene_symbol, entrez_gene_id, omim_gene_id))

            else:
                log.warn('Failed to get gene_id2gene_symbol EntrezGeneID: {0}'.format(entrez_gene_id))

                result.append(_gene(None, entrez_gene_id, None))

        return result
