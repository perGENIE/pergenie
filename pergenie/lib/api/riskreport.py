import sys, os
import re
import datetime
from pymongo import MongoClient
from django.conf import settings
from lib.api.gwascatalog import GWASCatalog
gwascatalog = GWASCatalog()
from lib.api.genomes import Genomes
genomes = Genomes()
from utils import clogging
log = clogging.getColorLogger(__name__)


class RiskReport(object):
    def __init__(self):
        pass

    def is_uptodate(self, info):
        """Check if user's risk report is up-to-date.
        """
        with MongoClient(host=settings.MONGO_URI) as c:
            db = c['pergenie']
            user_data_info = db['data_info'].find_one({'user_id': info['user_id'], 'name': info['name']})
            last_riskreport_date = user_data_info.get('riskreport')

            if not last_riskreport_date:
                return False

            latest_gwascatalog_date = db['catalog_info'].find_one({'status': 'latest'})['date']
            delta_days = (latest_gwascatalog_date - last_riskreport_date).days

            return bool(delta_days < settings.UPDATE_SPAN)

    def import_riskreport(self, info):
        if info['user_id'].startswith(settings.DEMO_USER_ID): info['user_id'] = settings.DEMO_USER_ID

        # Get GWAS Catalog records for this population
        population = 'population:{0}'.format('+'.join(settings.POPULATION_MAP[info['population']]))
        catalog_records = gwascatalog.search_catalog_by_query(population, None).sort('trait', 1)
        catalog_map = {}
        found_id = 0
        snps_all = set()
        for record in catalog_records:
            if record['snps'] != 'na':
                snps_all.update([record['snps']])

                found_id += 1
                reported_genes = ', '.join([gene['gene_symbol'] for gene in record['reported_genes']])
                mapped_genes = ', '.join([gene['gene_symbol'] for gene in record['mapped_genes']])
                catalog_map[found_id] = record
                catalog_map[found_id].update({'rs': record['snps'],
                                              'reported_genes': reported_genes,
                                              'mapped_genes': mapped_genes,
                                              'chr': record['chr_id'],
                                              'freq': record['risk_allele_frequency'],
                                              'added': record['added'].date(),
                                              'date': record['date'].date()})

        # Get genotypes for these GWAS Catalog records
        # Case1: in catalog & in variants
        variants_map = genomes.get_genotypes(info['user_id'], info['name'], info['file_format'], list(snps_all), 'rs',
                                             check_ref_or_not=False)

        # Case2: in catalog, but not in variants. so genotype is homozygous of `ref` or `na`.
        for _id, _catalog in catalog_map.items():
            rs = _catalog['rs']
            if rs and rs != 'na' and (not rs in variants_map):
                variants_map[rs] = genomes._ref_or_na(rs, 'rs', info['file_format'], rec=_catalog)

        # Case3: TODO:

        # Get number of uniq studies for this population
        # & Get cover rate of GWAS Catalog for this population
        uniq_studies, uniq_snps = set(), set()
        n_available = 0
        for record in catalog_map.values():
            if not record['pubmed_id'] in uniq_studies:
                uniq_studies.update([record['pubmed_id']])

            if record['snp_id_current'] and record['snp_id_current'] not in uniq_snps:
                uniq_snps.update([record['snp_id_current']])

                if info['file_format'] == 'vcf_exome_truseq' and record['is_in_truseq']:
                    n_available += 1
                elif info['file_format'] == 'vcf_exome_iontargetseq' and record['is_in_iontargetseq']:
                    n_available += 1
                elif info['file_format'] == 'andme' and record['is_in_andme']:
                    n_available += 1

        log.debug('n_available: %s' % n_available)

        n_studies = len(uniq_studies)
        if info['file_format'] == 'vcf_whole_genome':
            catalog_cover_rate_for_this_population = 100
        else:
            catalog_cover_rate_for_this_population = round(100 * n_available / len(uniq_snps))

        # Calculate risk
        risk_store, risk_reports = self.risk_calculation(catalog_map, variants_map,
                                                         settings.POPULATION_MAP[info['population']],
                                                         info['user_id'], info['name'], False)

        # Set reliability rank
        tmp_risk_reports = dict()
        for trait,studies in risk_reports.items():
            tmp_risk_reports[trait] = {}

            for study,value in studies.items():
                record = risk_store[trait][study].values()[0]['catalog_map']
                r_rank = self._calc_reliability_rank(record)
                tmp_risk_reports[trait].update({study: [r_rank, value]})
        risk_reports = tmp_risk_reports

        # Import riskreport into MongoDB
        with MongoClient(host=settings.MONGO_URI) as c:
            users_reports = c['pergenie']['reports'][info['user_id']][info['name']]
            if users_reports.find_one():
                c['pergenie'].drop_collection(users_reports)

            for trait, study_level_rank_and_values in risk_reports.items():
                # Get highest reriability study
                studies = list()
                for study, rank_and_values in study_level_rank_and_values.items():
                    studies.append(dict(study=study, rank=rank_and_values[0], RR=rank_and_values[1]))
                highest = self._get_highest_priority_study(studies)

                # Get SNP level infos (RR, genotype, etc...)
                snp_level_records = list()
                for study, snp_level_sotres in risk_store[trait].items():
                    for snp, snp_level_sotre in snp_level_sotres.items():
                        snp_level_records.append(dict(snp=snp,
                                                      RR=snp_level_sotre['RR'],  # snp-level
                                                      genotype=snp_level_sotre['variant_map'],  # snp-level
                                                      study=study,
                                                      rank=study_level_rank_and_values.get(study, ['na'])[0]  # study-level  # FIXME: why key-error occur?
                                                  ))

                users_reports.insert(dict(trait=trait,
                                          RR=highest['RR'],
                                          rank=highest['rank'],
                                          highest=highest['study'],
                                          studies=snp_level_records), upsert=True)

            # Update data_info
            data_info = c['pergenie']['data_info']
            data_info.update({'user_id': info['user_id'], 'name': info['name']},
                             {"$set": {'riskreport': datetime.datetime.today(),
                                       'n_studies': n_studies,
                                       'catalog_cover_rate_for_this_population': catalog_cover_rate_for_this_population}}, upsert=True)

    def risk_calculation(self, catalog_map, variants_map, population, user_id, file_name, is_LD_block_clustered):
        """
        Calculate risk

        Notes:
          * use **cumulative model**
          * zygosities are determied by number of risk alleles
        """

        risk_store = {}
        risk_report = {}

        for found_id in catalog_map:
            record = catalog_map[found_id]
            rs = record['rs']
            variant = variants_map[rs]

            # Filter out odd records
            while True:
                tmp_risk_data = {'catalog_map': record, 'variant_map': variant, 'zyg': None, 'RR': None}

                if not record['risk_allele'] in ['A', 'T', 'G', 'C']: break
                if not record['freq']: break

                try:
                    if not float(record['OR_or_beta']) > 1:
                        break
                except (TypeError, ValueError):
                    break

                # Store records by trait by study
                if not record['trait'] in risk_store:
                    risk_store[record['trait']] = {record['study']: {rs: tmp_risk_data}} # initial record

                else:
                    if not record['study'] in risk_store[record['trait']]:
                        risk_store[record['trait']][record['study']] = {rs: tmp_risk_data} # after initial record

                    else:
                        risk_store[record['trait']][record['study']][rs] = tmp_risk_data

                break

        for trait in risk_store:
            for study in risk_store[trait]:
                for rs in risk_store[trait][study]:
                    risk_store[trait][study][rs]['zyg'] = self._zyg(risk_store[trait][study][rs]['variant_map'],
                                                                    risk_store[trait][study][rs]['catalog_map']['risk_allele'])

                    RR, R = self._relative_risk_to_general_population(risk_store[trait][study][rs]['catalog_map']['freq'],
                                                                      risk_store[trait][study][rs]['catalog_map']['OR_or_beta'],
                                                                      risk_store[trait][study][rs]['zyg'])

                    risk_store[trait][study][rs]['RR'] = RR
                    risk_store[trait][study][rs]['R'] = R

                    if not trait in risk_report:
                        risk_report[trait] = {study: RR}  # initial
                    else:
                        if not study in risk_report[trait]:
                            risk_report[trait][study] = RR  # after initial
                        else:
                            risk_report[trait][study] *= RR

        return risk_store, risk_report

    def to_signed_real(self, records, is_log=False):
        """
        >>> records = [{'RR': -1.0}, {'RR': 0.0}, {'RR': 0.1}, {'RR': 1.0}]
        >>> print _to_signed_real(records)
        [{'RR': -10.0}, {'RR': 1.0}, {'RR': 1.3}, {'RR': 10.0}]
        """
        results = []

        for record in records:
            tmp_record = record

            if is_log:
                # Convert to real
                tmp_record['RR'] = pow(10, record['RR'])

            # If RR is negative effects, i.e, 0.0 < RR < 1.0,
            # inverse it and minus sign
            if 0.0 < tmp_record['RR'] < 1.0:
                tmp_record['RR'] = -1.0 / record['RR']
            elif tmp_record['RR'] == 0.0:
                tmp_record['RR'] = 1.0
            else:
                tmp_record['RR'] = record['RR']

            tmp_record['RR'] = round(tmp_record['RR'], 1)

            results.append(tmp_record)

        return results

    def _calc_reliability_rank(self, record):
        """
        >>> record = {'study': 'a', 'p_value': '1e-10'}
        >>> calc_reliability_rank(record)
        '***'
        >>> record = {'study': 'a', 'p_value': '1e-7'}
        >>> calc_reliability_rank(record)
        '**'
        >>> record = {'study': 'a', 'p_value': '1e-4'}
        >>> calc_reliability_rank(record)
        '*'
        >>> record = {'study': 'a', 'p_value': '1e-1'}
        >>> calc_reliability_rank(record)
        ''
        >>> record = {'study': 'a', 'p_value': '0.0'}
        >>> calc_reliability_rank(record)
        ''
        >>> record = {'study': 'Meta-analysis of a', 'p_value': '1e-10'}
        >>> calc_reliability_rank(record)
        'm***'
        >>> record = {'study': 'meta-analysis of a', 'p_value': '1e-10'}
        >>> calc_reliability_rank(record)
        'm***'
        >>> record = {'study': 'meta analysis of a', 'p_value': '1e-10'}
        >>> calc_reliability_rank(record)
        'm***'
        >>> record = {'study': 'a meta analysis of a', 'p_value': '1e-10'}
        >>> calc_reliability_rank(record)
        'm***'
        """

        r_rank = ''

        # is Meta-Analysis of GWAS ?
        if re.search('meta.?analysis', record['study'], re.IGNORECASE):
            r_rank += 'm'

        """
        * p-value based reliability rank:

        |   4   5   6   7   8   9   |
        |   |   |   |   |   |   | * |
        |   |   |   | * | * | * | * |
        |   | * | * | * | * | * | * |

        """

        if record['p_value']:
            res = re.findall('(\d+)e-(\d+)', record['p_value'], re.IGNORECASE)

            if not res:
                pass
            else:
                b = float(res[0][1])
                if b < 4:
                    pass
                elif 4 <= b < 6:
                    r_rank += '*'
                elif 6 <= b < 9:
                    r_rank += '**'
                elif 9 <= b:
                    r_rank += '***'

        # sample size:
        # TODO: parse sample-size
        # TODO: check the correlation `sample size` and `p-value`
        # if record['initial_sample_size']:

        return r_rank

    def _get_highest_priority_study(self, studies):
        """
        >>> data = [{'study': 'a', 'rank': '**', 'RR': 1.0}, \
                    {'study': 'b', 'rank': '*', 'RR': 1.0}]
        >>> get_highest_priority_study(data)
        {'study': 'a', 'RR': 1.0, 'rank': '**'}

        >>> data = [{'study': 'a', 'rank': 'm**', 'RR': 1.0}, \
                    {'study': 'b', 'rank': '*', 'RR': 1.0}]
        >>> get_highest_priority_study(data)
        {'study': 'a', 'RR': 1.0, 'rank': 'm**'}

        >>> data = [{'study': 'a', 'rank': 'm**', 'RR': 1.0}, \
                    {'study': 'b', 'rank': 'm*', 'RR': 1.0}]
        >>> get_highest_priority_study(data)
        {'study': 'a', 'RR': 1.0, 'rank': 'm**'}

        >>> data = [{'study': 'a', 'rank': '**', 'RR': 1.0}, \
                    {'study': 'b', 'rank': 'm*', 'RR': 1.0}]
        >>> get_highest_priority_study(data)
        {'study': 'b', 'RR': 1.0, 'rank': 'm*'}

        """

        highest = None

        for record in studies:
            if not highest:
                highest = record

            elif record['rank'].count('*') > highest['rank'].count('*'):
                if ('m' in highest['rank']) and (not 'm' in record['rank']):
                    pass
                else:
                    highest = record
            elif (not 'm' in highest['rank']) and ('m' in record['rank']):
                highest = record

        return highest

    def _zyg(self, genotype, risk_allele):
        """
        >>> _zyg('na', '')
        'NA'
        >>> _zyg('AA', 'A')
        'RR'
        >>> _zyg('AT', 'A')
        'R.'
        >>> _zyg('TT', 'A')
        '..'
        """

        if genotype == 'na':
            return 'NA'

        try:
            return {0:'..', 1:'R.', 2:'RR'}[genotype.count(risk_allele)]
        except TypeError:
            log.warn('genotype?? genotype:{0} risk-allele {1} '.format(genotype, risk_allele))  ###
            return '..'

    def _relative_risk_to_general_population(self, freq, OR, zygosities):
        """
        >>> _relative_risk_to_general_population(0.28, 1.37, 'NA')
        (1.0, 1.22)
        >>> _relative_risk_to_general_population(0.28, 1.37, 'RR')
        (1.5, 1.22)
        >>> _relative_risk_to_general_population(0.28, 1.37, 'R.')
        (1.1, 1.22)
        >>> _relative_risk_to_general_population(0.28, 1.37, '..')
        (0.8, 1.22)
        """

        try:
            prob_hom = freq**2
            prob_het = 2*freq*(1-freq)
            prob_ref = (1-freq)**2

            OR_hom = OR**2
            OR_het = OR
            OR_ref = 1.0

            average_population_risk = prob_hom*OR_hom + prob_het*OR_het + prob_ref*OR_ref

            risk_hom = OR_hom/average_population_risk
            risk_het = OR_het/average_population_risk
            risk_ref = OR_ref/average_population_risk

        except TypeError:
            return 1.0, 1.0  ###

        return round({'RR':risk_hom, 'R.':risk_het, '..':risk_ref, 'NA': 1.0}.get(zygosities, 1.0), 1), round(average_population_risk, 2)


def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()
