#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import argparse
import os
import csv
import datetime
import time
import re
import sys
import pymongo
try:
   import cPickle as pickle
except ImportError:
   import pickle

import weblio_eng2ja
import colors

_g_gene_symbol_map = {}  # { Gene Symbol => (Entrez Gene ID, OMIM Gene ID) }
_g_gene_id_map = {}      # { Entrez Gene ID => (Gene Symbol, OMIM Gene ID) }

def pickle_dump_obj(obj, fout_name):
    with open(fout_name, 'wb') as fout:
        pickle.dump(obj, fout, protocol=2)

def pickle_load_obj(fin_name):
    with open(fin_name, 'rb') as fin:
        obj = pickle.load(fin)
    return obj

def import_catalog(path_to_gwascatalog, path_to_mim2gene, path_to_pickled_catalog=None):
    print 'Loading mim2gene.txt...'
    with open(path_to_mim2gene, 'rb') as fin:
        for record in csv.DictReader(fin, delimiter='\t'):
            gene_type = record['Type'].lower()
            if gene_type.find('gene') < 0: continue

            omim_gene_id = record['# Mim Number']
            entrez_gene_id = record['Gene IDs']
            gene_symbol = record['Approved Gene Symbols']

            _g_gene_symbol_map[gene_symbol] = entrez_gene_id, omim_gene_id
            _g_gene_id_map[entrez_gene_id] = gene_symbol, omim_gene_id


    # print 'Loading eng2ja.txt...'
    # eng2ja = {}
    # with open(path_to_eng2ja, 'rb') as fin:
    #     for record in csv.DictReader(fin, delimiter='/'):
    #         eng2ja[record['eng']] = record['ja']
    eng2ja = weblio_eng2ja.WeblioEng2Ja('data/eng2ja.txt', 'data/eng2ja_plus.txt')

    with pymongo.Connection() as connection:
        catalog = connection['pergenie']['catalog']
        dbsnp = connection['dbsnp']['B132']  #
        
        # ensure db.catalog does not exist
        if catalog.find_one():
            connection['pergenie'].drop_collection(catalog)
            print '[WARNING] dropped old collection'
        assert catalog.count() == 0

        if not dbsnp.find_one():
            print '[WARNING] dbsnp.B132 does not exist in mongodb ...'
            print '[WARNING] so strand-check will be skipped'
            dbsnp = None

        # can load from pickled catalog
        if path_to_pickled_catalog:
           print '[WARNING] try to load catalog from {}...'.format(path_to_pickled_catalog)
           if os.path.exists(path_to_pickled_catalog):
              pickled_catalog = pickle_load_obj(path_to_pickled_catalog)
              for record in pickled_catalog:
                 catalog.insert(record)
              print '[INFO] import catalog done'
              return
           else:
              print '[WARNING] but does not exist'
              print '[WARNING] so load from flatfile {}'.format(path_to_gwascatalog)

        
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
                  ('study', 'Study', _string),
                  ('trait', 'Disease/Trait', _string),
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
                  ('p_value', 'p-Value', _float),
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
        print '[INFO] # of fields:', len(fields)

        print '[INFO] Importing gwascatalog.txt...'
        trait_dict = {}
        catalog_summary = {}
        to_pickle_catalog = []
        with open(path_to_gwascatalog, 'rb') as fin:
            for i,record in enumerate(csv.DictReader(fin, delimiter='\t')):# , quotechar="'"):
                print >>sys.stderr, i
                data = {}
                for dict_name, record_name, converter in fields:
                    try:
                        data[dict_name] = converter(record[record_name])
                    except KeyError:
                        pass

                # Weblio eng2ja
                data['eng2ja'] = eng2ja.try_get(data['trait'])

                if (not data['snps']) or (not data['strongest_snp_risk_allele']):
                    print colors.green('[WARNING] absence of "snps" or "strongest_snp_risk_allele" {0} {1}. pubmed_id:{2}'.format(data['snps'], data['strongest_snp_risk_allele'], data['pubmed_id']))
                else:

                    rs, data['risk_allele'] = _risk_allele(data['strongest_snp_risk_allele'], dbsnp)
                    if data['snps'] != rs:
                        print colors.red('[WARNING] "snps" != "risk_allele": {0} != {1}'.format(data['snps'], rs))

                    else:
                        try:
                            trait_dict[data['trait']] += 1
                        except KeyError:
                            trait_dict[data['trait']] = 1


                        # identfy OR or beta & TODO: convert beta to OR if can
                        data['OR'] = identfy_OR_or_beta(data['OR_or_beta'], data['CI_95'])


                        # for DEGUG
                        if type(data['OR']) == float:
                           data['OR_or_beta'] = data['OR']
                           print data['OR_or_beta'], data['OR'], 'rs{}'.format(data['snps'])
                        else:
                           data['OR_or_beta'] = None


                        # catalog summary
                        # TODO: support gene records
                        for field,value in data.items():
                            if '_gene' in field or field == 'CI_95':
                                pass
                            else:
                                try:
                                    catalog_summary[field][value] += 1
                                except KeyError:

                                    try:
                                        catalog_summary[field].update({value: 1})
                                    except KeyError:
                                        catalog_summary[field] = {value: 1}

                        to_pickle_catalog.append(data)
                        catalog.insert(data)

            # TODO: indexing target
            # catalog.create_index([('snps', pymongo.ASCENDING)])

    # for trait,ok_count in sorted(trait_dict.items(), key=lambda x:x[1]):
    #     print '[INFO]', trait, ok_count
            
    print '[INFO] # of traits:', len(trait_dict)
    print '[INFO] # of documents in catalog (after):', catalog.count()
    
    pickle_dump_obj(catalog_summary, 'catalog_summary.p')
    pickle_dump_obj(field_names, 'field_names.p')
    pickle_dump_obj(to_pickle_catalog, 'catalog.p')
    print '[INFO] dumped catalog_summary.p as pickle'
    print '[INFO] dumped field_names.p as pickle'
    print '[INFO] dumped catalog.p as pickle'

    # write out my_trait_list & my_trait_list_ja
    with open('my_trait_list.py', 'w') as my_trait_list:
        trait_list = [k for k in trait_dict.keys()]
        print >>my_trait_list, '# -*- coding: utf-8 -*- '
        print >>my_trait_list, 'my_trait_list =',
        print >>my_trait_list,  trait_list  

        trait_list_ja = [eng2ja.try_get(trait) for trait in trait_list]
        print >>my_trait_list, ''
        print >>my_trait_list, 'my_trait_list_ja =',
        print >>my_trait_list,  trait_list_ja

    print '[INFO] import catalog done'
    return

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
                  print '{0} {1} {2}'.format(text, texts[0][0], CIs)
                  if CIs[0] == '' and CIs[1] == '-' and CIs[3] == '-':  # [-2.13040-19.39040]
                     result['CI'] = [(-1)*float(CIs[2]), float(CIs[4])]
                  else:
                     print  '{0} {1}'.format(text, texts)
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
            value =  float(text)
        except ValueError:
            match = re.match('\d*\.\d+', text)
            if match:
                value = float(match.group())
            else:
                print >>sys.stderr, 'OR_or_beta? {}'.format(text)
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
            msg = '[WARNING] in _rss, more than one rs: {}'
            print >>sys.stderr, msg.format(text)
            return None   # 

        try:
            return int(text.replace('rs', ''))
        except ValueError:
            msg = '[WARNING] in _rss, failed to convert to int: {}'
            print >>sys.stderr, msg.format(text)
            return None   # 


def _risk_allele(text, dbsnp):
    """
    * use strongest_snp_risk_allele in GWAS Catalog as risk allele, e.g., rs331615-T -> T
    * check if is in dbSNP REF,ALT considering RV; (if dbsnp.B132 is available)
    """

    reg_risk_allele = re.compile('rs(\d+)\-(\S+)')
    RV_map = {'A':'T', 'T':'A', 'G':'C', 'C':'G'}

    if not text or text in ('NR', 'NS'):
        return None, None

    else:
        try:
            rs, risk_allele = reg_risk_allele.findall(text)[0]
        except (ValueError, IndexError):
            print '[WARNING] failed to parse "strongest_snp_risk_allele": {}'.format(text)
            return text, None

        #
        if risk_allele == '?':
            # print colors.green('[WARNING] allele is "?": {}'.format(text))
            return int(rs), risk_allele


        if not risk_allele in ('A', 'T', 'G', 'C'):
            print colors.green('[WARNING] allele is not (A,T,G,C): {}'.format(text))
            return text, None

        # *** Check if record is in dbSNP REF, ALT ***
        else:
            # Check if record is in dbSNP (if dbsnp is available)
            if dbsnp:
                tmp_rs_record = list(dbsnp.find({'rs':int(rs)}))
                if not tmp_rs_record:
                    print colors.black('rs{0} is not in dbSNP ...').format(rs)
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
                            print colors.yellow('[WARNING] for {0}, {1}(RV) is in REF:{2}, ALT:{3}, so return RVed. rs{4}'.format(risk_allele, rev_risk_allele, ref, alt, rs))
                            risk_allele = rev_risk_allele

                        else:
                            print colors.red('[WARNING] both {0} and {1}(RV) are not in REF:{2}, ALT:{3} ... rs{4}'.format(risk_allele, rev_risk_allele, ref, alt, rs))
                            risk_allele += '?'

                    # Although not RV, challenge supposing as RV
                    else:
                        print colors.blue('[WARNING] {0} is not in REF:{1}, ALT:{2} and not RV, '.format(risk_allele, ref, alt)),
                        if rev_risk_allele in ref_alt:
                            print colors.purple('but somehow {0}(RV) is in REF, ALT ... rs{1}'.format(rev_risk_allele, rs))
                            risk_allele = rev_risk_allele + '?'

                        else:
                            print colors.red('and {0}(RV) is not in REF, ALT. rs{1}'.format(rev_risk_allele, rs))
                            risk_allele += '?'

        return int(rs), risk_allele


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
            if entrez_gene_id in _g_gene_id_map:
                gene_symbol, omim_gene_id = _g_gene_id_map[entrez_gene_id]
                result.append(_gene(gene_symbol, entrez_gene_id, omim_gene_id))

            else:
#                 msg = '[WARNING] Failed to find gene from mim2gene, EntrezGeneID: {}'
#                 print >>sys.stderr, msg.format(entrez_gene_id)

                result.append(_gene(None, entrez_gene_id, None))

        return result


def _main():
    parser = argparse.ArgumentParser(description='import gwascatalog.txt to the database')
    parser.add_argument('gwascatalog', help='path to gwascatalog.txt')
    parser.add_argument('mim2gene', help='path to mim2gene.txt')
    parser.add_argument('--pickled_catalog', help='path to pickled catalog')
    args = parser.parse_args()

    import_catalog(args.gwascatalog, args.mim2gene, args.pickled_catalog)

if __name__ == '__main__':
    _main()
