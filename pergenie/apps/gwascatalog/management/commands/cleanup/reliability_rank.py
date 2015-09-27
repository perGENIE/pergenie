def get_reliability_rank(study, p_value, sample_size=None):
    """
    >>> get_reliability_rank(study = 'a', p_value = '1e-10')
    '***'
    >>> get_reliability_rank(study = 'a', p_value = '1e-7')
    '**'
    >>> get_reliability_rank(study = 'a', p_value = '1e-4')
    '*'
    >>> get_reliability_rank(study = 'a', p_value = '1e-1')
    ''
    >>> get_reliability_rank(study = 'a', p_value = '0.0')
    ''
    >>> get_reliability_rank(study = 'Meta-analysis of a', p_value = '1e-10')
    'm***'
    >>> get_reliability_rank(study = 'meta-analysis of a', p_value = '1e-10')
    'm***'
    >>> get_reliability_rank(study = 'meta analysis of a', p_value = '1e-10')
    'm***'
    >>> get_reliability_rank(study = 'a meta analysis of a', p_value = '1e-10')
    'm***'
    """

    r_rank = ''

    # is Meta-Analysis of GWAS ?
    if re.search('meta.?analysis', study, re.IGNORECASE):
        r_rank += 'm'

    """
    * p-value based reliability rank:

    |   4   5   6   7   8   9   |
    |   |   |   |   |   |   | * |
    |   |   |   | * | * | * | * |
    |   | * | * | * | * | * | * |

    """

    if p_value:
        res = re.findall('(\d+)e-(\d+)', p_value, re.IGNORECASE)

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

    # TODO:
    if sample_size:
        pass

    return r_rank
