# -*- coding: utf-8 -*-

import sys, os
import re
import csv
import datetime
import time
import json
import pymongo
from extract_region import extract_region

from utils.io import pickle_dump_obj
from utils import clogging
log = clogging.getColorLogger(__name__)

_g_gene_symbol_map = {}  # { Gene Symbol => (Entrez Gene ID, OMIM Gene ID) }
_g_gene_id_map = {}      # { Entrez Gene ID => (Gene Symbol, OMIM Gene ID) }


def import_catalog(path_to_gwascatalog, path_to_mim2gene, path_to_eng2ja, path_to_disease2wiki, path_to_interval_list_dir,
                   catalog_summary_cache_dir, mongo_port):
    c = pymongo.MongoClient(port=mongo_port)

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
    log.debug('Loading {} ...'.format(path_to_eng2ja))
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
    dbsnp = c['dbsnp']['B132']

    # ensure db.catalog does not exist
    if catalog.find_one():
        c['pergenie'].drop_collection(catalog)
        log.info('dropped old collection')
    assert catalog.count() == 0

    if not dbsnp.find_one():
        log.warn('========================================')
        log.warn('dbsnp.B132 does not exist in mongodb ...')
        log.warn('so strand-check will be skipped')
        log.warn('========================================')
        dbsnp = None

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
    log.info('# of fields: {}'.format(len(fields)))

    log.debug('Importing gwascatalog.txt...')
    catalog_summary = {}
    with open(path_to_gwascatalog, 'rb') as fin:
        for i,record in enumerate(csv.DictReader(fin, delimiter='\t')):# , quotechar="'"):

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

            if (not data['snps']) or (not data['strongest_snp_risk_allele']):
                log.warn('absence of "snps" or "strongest_snp_risk_allele" {0} {1}. pubmed_id:{2}'.format(data['snps'], data['strongest_snp_risk_allele'], data['pubmed_id']))
                data['snps'], data['strongest_snp_risk_allele'], data['risk_allele'] = 'na', 'na', 'na'
                catalog.insert(data)
            else:

                rs, data['risk_allele'] = _risk_allele(data['strongest_snp_risk_allele'], dbsnp)
                if data['snps'] != rs:
                    log.warn('"snps" != "risk_allele": {0} != {1}'.format(data['snps'], rs))
                    catalog.insert(data)

                else:
                    # identfy OR or beta & TODO: convert beta to OR if can
                    data['OR'] = identfy_OR_or_beta(data['OR_or_beta'], data['CI_95'])

                    # for DEGUG
                    if type(data['OR']) == float:
                        data['OR_or_beta'] = data['OR']
                        # print data['OR_or_beta'], data['OR'], 'rs{}'.format(data['snps'])
                    else:
                        data['OR_or_beta'] = None

                    # TODO: support gene records
                    for field,value in data.items():
                        if '_gene' in field or field == 'CI_95':
                            pass

                        else:
                            if type(value) == list:
                                value = str(value)
                            try:
                                catalog_summary[field][value] += 1
                            except KeyError:

                                try:
                                    catalog_summary[field].update({value: 1})
                                except KeyError:
                                    catalog_summary[field] = {value: 1}


                    # TODO: call `add_record_reliability`
                    # add_record_reliability(data)

                    catalog.insert(data)

        # TODO: indexing target
        # catalog.create_index([('snps', pymongo.ASCENDING)])

    log.info('# of documents in catalog (after): {}'.format(catalog.count()))

    # Add `is_in_truseq`, `is_in_andme` flags
    n_records, n_truseq, n_andme = 0, 0, 0
    for chrom in [i + 1 for i in range(24)]:
        log.info('Addding flags... chrom: {}'.format(chrom))
        records = list(catalog.find({'chr_id': chrom}).sort('chr_pos', pymongo.ASCENDING))
        n_records += len(records)
        log.info('records:{}'.format(n_records))

        # `is_in_truseq`
        region_file = os.path.join(path_to_interval_list_dir,
                                   'TruSeq-Exome-Targeted-Regions-BED-file.{}.interval_list'.format({23:'X', 24:'Y'}.get(chrom, chrom)))
        with open(region_file, 'r') as fin:
            extracted = extract_region(region_file, records)
            n_truseq += len(extracted)
            log.info('`is_in_truseq` extracted:{}'.format(n_truseq))
            for record in extracted:
                catalog.update(record, {"$set": {'is_in_truseq': True}})

        # `is_in_andme`
        region_file = os.path.join(path_to_interval_list_dir,
                                   'andme_region.{}.interval_list'.format({23:'X', 24:'Y', 25:'MT'}.get(chrom, chrom)))
        with open(region_file, 'r') as fin:
            extracted = extract_region(region_file, records)
            n_andme += len(extracted)
            log.info('`is_in_andme` extracted:{}'.format(n_andme))
            for record in extracted:
                catalog.update(record, {"$set": {'is_in_andme': True}})

    stats = {'catalog_cover_rate': {'vcf_whole_genome': 100,
                                    'vcf_exome_truseq': int(round(100 * n_truseq / n_records)),
                                    'andme': int(round(100 * n_andme / n_records))}}
    log.info(stats)

    catalog_stats = c['pergenie']['catalog_stats']
    if catalog_stats.find_one():
        c['pergenie'].drop_collection(catalog_stats)

    catalog_stats.insert(stats)

    log.info('catalog.find_one(): {}'.format(catalog.find_one()))

    # dump as pickle (always overwrite)
    pickle_dump_obj(catalog_summary, os.path.join(catalog_summary_cache_dir, 'catalog_summary.p'))
    pickle_dump_obj(field_names, os.path.join(catalog_summary_cache_dir, 'field_names.p'))
    log.info('dumped catalog_summary.p, field_names.p as pickle')

    trait_list = list(catalog_summary['trait'])
    trait_list_ja = [eng2ja.get(trait, trait) for trait in list(catalog_summary['trait'])]
    pickle_dump_obj(trait_list, os.path.join(catalog_summary_cache_dir, 'trait_list.p'))
    pickle_dump_obj(trait_list_ja, os.path.join(catalog_summary_cache_dir, 'trait_list_ja.p'))
    log.info('dumped trait_list.p, trait_list_ja.p as pickle')

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
        OR = 'beta:{}'.format(OR_or_beta)

    else:
        if OR_or_beta:
            OR = float(OR_or_beta)

            #
            if OR < 1.0:  # somehow beta without text in 95% CI ?
                OR = 'beta:{}?'.format(OR_or_beta)

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
                log.warn('OR_or_beta? {}'.format(text))
                return None

        return value
        # if value >= 1.0:
        #     return value

        # else:
        #     print >>sys.stderr, 'OR_or_beta? {}'.format(text)
        #     return text+'?'


def _rss(text):
    """
    TODO: support multiple rss records. (temporary, if multiple rss, rss = None)
    """

    if not text or text in ('NR', 'NS'):
        return None

    else:
        if len(text.split(',')) != 1:
            log.warn('in _rss, more than one rs: {}'.format(text))
            return None   #

        try:
            return int(text.replace('rs', ''))
        except ValueError:
            log.warn('in _rss, failed to convert to int: {}'.format(text))
            return None   #


def _risk_allele(text, dbsnp):
    """
    * use strongest_snp_risk_allele in GWAS Catalog as risk allele, e.g., rs331615-T -> T
    * check if is in dbSNP REF,ALT considering RV; (if dbsnp.B132 is available)
    """

    reg_risk_allele = re.compile('rs(\d+)\-(\S+)')
    RV_map = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}

    if not text or text in ('NR', 'NS'):
        return None, None

    else:
        try:
            rs, risk_allele = reg_risk_allele.findall(text)[0]
        except (ValueError, IndexError):
            log.warn('failed to parse "strongest_snp_risk_allele": {}'.format(text))
            return text, None

        #
        if risk_allele == '?':
            # log.warn('allele is "?": {}'.format(text))
            return int(rs), risk_allele

        if not risk_allele in ('A', 'T', 'G', 'C'):
            log.warn('allele is not (A,T,G,C): {}'.format(text))
            return text, None

        # *** Check if record is in dbSNP REF, ALT ***
        else:
            # Check if record is in dbSNP (if dbsnp is available)
            if dbsnp:
                tmp_rs_record = list(dbsnp.find({'rs': int(rs)}))
                if not tmp_rs_record:
                    log.warn('rs{0} is not in dbSNP ...'.format(rs))
                    return int(rs), risk_allele + '?'
                assert len(tmp_rs_record) < 2, text

                ref, alt = tmp_rs_record[0]['ref'], tmp_rs_record[0]['alt']
                ref_alt = ref.split(',') + alt.split(',')

                # Check if record is in REF,ALT
                if risk_allele in (ref, alt):
                    pass

                else:
                    # Challenge considering RV case
                    rev_risk_allele = RV_map[risk_allele]
                    if 'RV' in tmp_rs_record[0]['info']:
                        if rev_risk_allele in ref_alt:
                            log.warn('for {0}, {1}(RV) is in REF:{2}, ALT:{3}, so return RVed. rs{4}'.format(risk_allele, rev_risk_allele, ref, alt, rs))
                            risk_allele = rev_risk_allele

                        else:
                            log.warn('both {0} and {1}(RV) are not in REF:{2}, ALT:{3} ... rs{4}'.format(risk_allele, rev_risk_allele, ref, alt, rs))
                            risk_allele += '?'

                    # Although not RV, challenge supposing as RV
                    else:
                        log.warn('{0} is not in REF:{1}, ALT:{2} and not RV, '.format(risk_allele, ref, alt))
                        if rev_risk_allele in ref_alt:
                            log.warn('but somehow {0}(RV) is in REF, ALT ... rs{1}'.format(rev_risk_allele, rs))
                            risk_allele = rev_risk_allele + '?'

                        else:
                            log.warn('and {0}(RV) is not in REF, ALT. rs{1}'.format(rev_risk_allele, rs))
                            risk_allele += '?'

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
#             msg = '[WARNING] Failed to convert to float, Text: {}'
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
        # avoid slash
        # if '/' in text:
        #     log.warn('/ in {}'.format(text))
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
#                 msg = '[WARNING] Failed to find gene from mim2gene, GeneSymbol: {}'
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
#             msg = '[WARNING] Failed to find gene from mim2gene, EntrezGeneID: {}'
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
                log.warn('Failed to get gene_id2gene_symbol EntrezGeneID: {}'.format(entrez_gene_id))

                result.append(_gene(None, entrez_gene_id, None))

        return result
