import re


class RiskReportBase(object):
    """
    Base Class for RiskReport

    - No Django dependency
    - No MongoDB dependency
    """

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
            print 'genotype?? genotype:{0} risk-allele {1} '.format(genotype, risk_allele)  ###
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
