# -*- coding: utf-8 -*-

import re

def calc_reliability_rank(record):
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

    # p-value based reliability rank:
    #
    #      4   5   6   7   8   9
    # |    |   |   |   |   |   | *
    # | NA |   |   | * | * | * | *
    # |    | * | * | * | * | * | *

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


def get_highest_priority_study(studies):
    """
    >>> data = {'a': ['**', 1.0], 'b': ['*', 1.0]}
    >>> get_highest_priority_study(data)
    {'study': 'a', 'value': 1.0', rank': '**'}

    >>> data = {'a': ['m**', 1.0], 'b': ['*', 1.0]}
    >>> get_highest_priority_study(data)
    {'study': 'a', 'value': 1.0, 'rank': 'm**'}

    >>> data = {'a': ['m**', 1.0], 'b': ['m*', 1.0]}
    >>> get_highest_priority_study(data)
    {'study': 'a', 'value': 1.0, 'rank': 'm**'}

    >>> data = {'a': ['**', 1.0], 'b': ['m*', 1.0]}
    >>> get_highest_priority_study(data)
    {'study': 'b', 'value': 1.0, 'rank': 'm*'}

    """

    highest = dict(study='', rank='', value=0.0)

    for study,[rank,value] in studies.items():
        record = dict(study=study, rank=rank, value=value)

        if rank.count('*') > highest['rank'].count('*'):
            if ('m' in highest['rank']) and (not 'm' in rank):
                pass
            else:
                highest = record
        elif (not 'm' in highest['rank']) and ('m' in rank):
            highest = record

    return highest
