import re

from django.conf import settings

from pergenie.fasta import reference_genome_fasta
from lib.utils.genome import chr_id2chrom
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


def reliability_rank(record):
    """
    >>> record = {'study': 'a', 'p_value': '1e-10'}
    >>> reliability_rank(record)
    '***'
    >>> record = {'study': 'a', 'p_value': '1e-7'}
    >>> reliability_rank(record)
    '**'
    >>> record = {'study': 'a', 'p_value': '1e-4'}
    >>> reliability_rank(record)
    '*'
    >>> record = {'study': 'a', 'p_value': '1e-1'}
    >>> reliability_rank(record)
    ''
    >>> record = {'study': 'a', 'p_value': '0.0'}
    >>> reliability_rank(record)
    ''
    >>> record = {'study': 'Meta-analysis of a', 'p_value': '1e-10'}
    >>> reliability_rank(record)
    'm***'
    >>> record = {'study': 'meta-analysis of a', 'p_value': '1e-10'}
    >>> reliability_rank(record)
    'm***'
    >>> record = {'study': 'meta analysis of a', 'p_value': '1e-10'}
    >>> reliability_rank(record)
    'm***'
    >>> record = {'study': 'a meta analysis of a', 'p_value': '1e-10'}
    >>> reliability_rank(record)
    'm***'
    """

    rank = ''

    # is Meta-Analysis of GWAS ?
    if re.search('meta.?analysis', record['study'], re.IGNORECASE):
        rank += 'm'

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
                rank += '*'
            elif 6 <= b < 9:
                rank += '**'
            elif 9 <= b:
                rank += '***'

    # sample size:
    # TODO: parse sample-size
    # TODO: check the correlation `sample size` and `p-value`
    # if record['initial_sample_size']:

    return rank


def population(text):
    """Parse `Initial Sample Size` in GWAS Catalog.

    Args:
    - `text`: value of `Initial Sample Size`

    Returns:
    - list of population strings, e.g., ['African', 'Asian', 'European']
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


def identfy_or_or_beta(OR_or_beta, CI_95):
    """
    >>> identfy_or_or_beta(None, None)
    (None, None)
    >>> identfy_or_or_beta(None, {'CI': [], 'text': ''})
    (None, None)
    >>> identfy_or_or_beta(10, {'CI': [], 'text': ''})
    (10, None)
    >>> identfy_or_or_beta(None, {'CI': [], 'text': 'unit increase'})
    (None, None)
    >>> identfy_or_or_beta(-1.0, {'CI': [], 'text': 'unit increase'})
    (None, -1.0)
    """
    OR, beta = None, None

    if CI_95 and CI_95['text']:
        beta = OR_or_beta
    else:
        if OR_or_beta > 1.0:  # OR are ajusted to >1.0 in GWAS Catalog
            OR = OR_or_beta

    return OR, beta


def risk_allele(data, snps=None):
    """

    Use strongest_snp_risk_allele in GWAS Catalog as risk allele,
    e.g., rs331615-T -> T

    Following checks will be done if available.

    * Consistency check based on allele frequency in SNPs database
      (dbSNP or 1000Genomes).

    """
    notes = ''
    gwascatalog_af_inconsistence_thrs = settings.GWASCATALOG_AF_INCONSISTENCE_THRS

    # Parse `strongest_snp_risk_allele`
    if not data['strongest_snp_risk_allele']:
        return None, None

    _risk_allele = re.compile('rs(\d+)\-(\S+)')
    try:
        rs, risk_allele = _risk_allele.findall(data['strongest_snp_risk_allele'])[0]
    except (ValueError, IndexError):
        log.warn('failed to parse "strongest_snp_risk_allele": {}'.format(data['strongest_snp_risk_allele']))
        log.warn(data)
        return None, None

    if risk_allele == '?':
        return int(rs), risk_allele

    if not risk_allele in ('A', 'T', 'G', 'C'):
        log.warn('allele is not in (A,T,G,C)')
        log.warn(data)
        return int(rs), None

    if not data['risk_allele_frequency']:
        return int(rs), risk_allele + '?'

    # Strand checks (if database is available)
    snp_database = snps

    if not snp_database:
        return int(rs), risk_allele

    else:
        RV = {'A': 'T', 'T': 'A', 'G': 'C', 'C': 'G'}
        population = data['population'][0] if data['population'] else 'European'  ## TODO: May be cause freq mismatch.
        rs = int(rs)
        # snp_summary = bq.get_snp_summary(rs)
        # ref = snp_summary['ancestral_alleles']
        allele_freqs, _ = snp_database.get_allele_freqs(rs, population=population)
        freqs = allele_freqs[population]

        # < Risk allele freq. X in Snpdb ? >
        freq = freqs.get(risk_allele)
        if freq:
            # < |freq_catalog(X) - freq_dbsnp(X))| <= thrs ? >
            diff = abs(freq['freq'] - data['risk_allele_frequency'])
            log.debug('diff: {diff}'.format(diff=diff))
            if diff <= gwascatalog_inconsistence_thrs:
                log.debug('ok')
                return int(rs), risk_allele, 'ok'
            else:
                log.warn('Inconsistence between GWAS Catalog and Snpdb')
                notes = 'Inconsistence between GWAS Catalog and Snpdb'
        else:
            log.warn('Snpdb freq for X not found')
            notes = 'Snpdb freq for X not found'

        # < Reversed risk allele freq. rev(X) in Snpdb ? >
        freq = freqs.get(RV[risk_allele])
        if not freq:
            log.warn(', but Snpdb freq for rev(X) not found')
            return int(rs), risk_allele + '?', notes + ', but Snpdb freq for rev(X) not found'

        # < |freq_catalog(rev(X)) - freq_dbsnp(rev(X)))| <= thrs ? >
        diff = abs(freq['freq'] - data['risk_allele_frequency'])
        log.debug('diff: {diff}'.format(diff=diff))
        if diff <= gwascatalog_inconsistence_thrs:
            log.info(', and solved with rev(X)')
            return int(rs), RV[risk_allele], notes + ', and solved with rev(X)'
        else:
            log.warn(', but not solved with rev(X)')
            return int(rs), risk_allele + '?', notes + ', but not solved with rev(X)'


def reference_allele(chr_id, chr_pos):
    if chr_id and chr_pos:
        ref = reference_genome_fasta.slice_fasta(chr_id2chrom(chr_id), chr_pos, chr_pos)
    else:
        ref = ''

    return ref


def pubmed_link(pubmed_id):
    return 'http://www.ncbi.nlm.nih.gov/pubmed/' + str(pubmed_id)


def dbsnp_link(snp_id):
    return 'http://www.ncbi.nlm.nih.gov/projects/SNP/snp_ref.cgi?rs=' + str(snp_id)
