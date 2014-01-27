from client import MySQLClient
from lib.utils import clogging
log = clogging.getColorLogger(__name__)


class Snps(MySQLClient):
    """
    >>> snpdb = Snps(settings.DATABASES['snps']['HOST'],
    >>>              settings.DATABASES['snps']['USER'],
    >>>              settings.DATABASES['snps']['PASSWORD'],
    >>>              settings.DATABASES['snps']['NAME'])

    dependancies:

    import following tables first:

    - ASN_allele_freq
    -
    -
    -

    """

    # def __init__(self):
    #     pass


    def _allele_freqs(self, population, rs):
        q = {'AFR': "select * from AFR_allele_freq where snp_id = %s",
             'ASN': "select * from ASN_allele_freq where snp_id = %s",
             'AMR': "select * from AMR_allele_freq where snp_id = %s",
             'EUR': "select * from EUR_allele_freq where snp_id = %s",
             'global': "select * from global_allele_freq where snp_id = %s"}[population]
        rows = self._sql(q, rs)
        return rows

    def _allele_freq_one(self, population, rs):
        """
        Returns:
        - dict
        """
        founds = self._allele_freqs(population, rs)

        if not founds:
            return dict()
        else:
            if len(founds) > 1:
                log.warn('{rs}: multiple founds (refSnp with multiple locus)'.format(rs))
            return list(founds)[0]  ## TODO: handle refSnp with multiple locus

    def get_allele_freqs(self, rs, population='unknown'):
        """

        Args:
        - rs <int>

        Returns:
        - {population: {alt_1: freq, alt_2: freq}} <dict>
        - uniq_alleles <set>

        Example:

        >>> snpdb = Snps()
        >>> snpdb.get_allele_freqs(3, 'European')
        {'European': {'A': {'freq': 0.10000000000000001}, 'G': {'freq': 0.90000000000000002}}}
        """

        population_map = {'African': 'AFR',
                          'European': 'EUR',
                          'Asian': 'ASN',
                          'Japanese': 'ASN',
                          'unknown': 'global'}

        if population == 'Japanese':
            log.warn('Currently, freq for Japanese is not accurate.')

        found = self._allele_freq_one(population_map[population], rs)
        if found:
            allele_freqs = {population: {found['alt_1']: {'freq': found['freq_alt_1']},
                                         found['alt_2']: {'freq': found['freq_alt_2']}}}
            uniq_alleles = set([found['freq_alt_1'], found['freq_alt_2']])
        else:
            allele_freqs = {population: {}}
            uniq_alleles = set()

        return allele_freqs, uniq_alleles
