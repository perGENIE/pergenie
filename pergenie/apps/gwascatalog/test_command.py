from django.test import TestCase
from django.conf import settings
from django.utils.translation import ugettext as _

from .management.commands.cleanup.risk_allele import get_forward_risk_allele


# TODO:
class GWASCatalogCommandTestCase(TestCase):
    def setUp(self):
        self.data = {'risk_allele': 'C',
                     'risk_allele_frequency': 0.1,
                     'population': ['European']}

    def test_allele_strand_check_ok(self):
        # Note:
        # It is odd if risk allele freq is equal to other allele. However, we accept as they are.

        for thrs in [0.0, 0.1]:
            # C(0.1) vs C(0.1)/T(0.9) => C
            self.data.update({'risk_allele_frequency': 0.1})
            freq = {'European': {'C': 0.1, 'T': 0.9}}
            risk_allele = get_forward_risk_allele(self.data['risk_allele'], self.data['risk_allele_frequency'], freq, thrs)
            self.assertEqual(risk_allele, 'C')
            self.assertEqual(notes, 'ok')

            # C(0.5) vs C(0.5)/T(0.5) => C
            self.data.update({'risk_allele_frequency': 0.5})
            freq = {'European': {'C': 0.5, 'T': 0.5}}
            risk_allele = get_forward_risk_allele(self.data['risk_allele'], self.data['risk_allele_frequency'], freq, thrs)
            self.assertEqual(risk_allele, 'C')
            self.assertEqual(notes, 'ok')

            # C(0.9) vs C(0.9)/T(0.1) => C
            self.data.update({'risk_allele_frequency': 0.9})
            freq = {'European': {'C': 0.9, 'T': 0.1}}
            risk_allele = get_forward_risk_allele(self.data['risk_allele'], self.data['risk_allele_frequency'], freq, thrs)
            self.assertEqual(risk_allele, 'C')
            self.assertEqual(notes, 'ok')

            # C(0.5) vs G(0.5)/C(0.5) => C
            self.data.update({'risk_allele_frequency': 0.5})
            freq = {'European': {'G': 0.5, 'C': 0.5}}
            risk_allele = get_forward_risk_allele(self.data['risk_allele'], self.data['risk_allele_frequency'], freq, thrs)
            self.assertEqual(risk_allele, 'C')
            self.assertEqual(notes, 'ok')

    def test_allele_strand_check_solved(self):
        for thrs in [0.0, 0.1]:
            # C(0.1) vs G(0.1)/A(0.9) => G
            self.data.update({'risk_allele_frequency': 0.1})
            freq = {'European': {'G': 0.1, 'A': 0.9}}
            risk_allele = get_forward_risk_allele(self.data['risk_allele'], self.data['risk_allele_frequency'], freq, thrs)
            self.assertEqual(risk_allele, 'G')
            self.assertEqual(notes, 'Snpdb freq for X not found, and solved with rev(X)')

            # C(0.5) vs G(0.5)/A(0.5) => G
            self.data.update({'risk_allele_frequency': 0.5})
            freq = {'European': {'G': 0.5, 'A': 0.5}}
            risk_allele = get_forward_risk_allele(self.data['risk_allele'], self.data['risk_allele_frequency'], freq, thrs)
            self.assertEqual(risk_allele, 'G')
            self.assertEqual(notes, 'Snpdb freq for X not found, and solved with rev(X)')

            # C(0.9) vs G(0.9)/A(0.1) => G
            self.data.update({'risk_allele_frequency': 0.9})
            freq = {'European': {'G': 0.9, 'A': 0.1}}
            risk_allele = get_forward_risk_allele(self.data['risk_allele'], self.data['risk_allele_frequency'], freq, thrs)
            self.assertEqual(risk_allele, 'G')
            self.assertEqual(notes, 'Snpdb freq for X not found, and solved with rev(X)')

            # C(0.1) vs G(0.1)/C(0.9) => G
            self.data.update({'risk_allele_frequency': 0.1})
            freq = {'European': {'G': 0.1, 'C': 0.9}}
            risk_allele = get_forward_risk_allele(self.data['risk_allele'], self.data['risk_allele_frequency'], freq, thrs)
            self.assertEqual(risk_allele, 'G')
            self.assertEqual(notes, 'Inconsistence between GWAS Catalog and Snpdb, and solved with rev(X)')

            # C(0.9) vs G(0.9)/C(0.1) => G
            self.data.update({'risk_allele_frequency': 0.9})
            freq = {'European': {'G': 0.9, 'C': 0.1}}
            risk_allele = get_forward_risk_allele(self.data['risk_allele'], self.data['risk_allele_frequency'], freq, thrs)
            self.assertEqual(risk_allele, 'G')
            self.assertEqual(notes, 'Inconsistence between GWAS Catalog and Snpdb, and solved with rev(X)')

    def test_allele_strand_check_unsolve_absence_of_freq_in_dbsnp(self):
        for thrs in [0.0, 0.1]:
            # C vs T/A => C?
            self.data.update({'risk_allele_frequency': 0.1})
            freq = {'European': {'T': 0.1, 'A': 0.9}}
            risk_allele = get_forward_risk_allele(self.data['risk_allele'], self.data['risk_allele_frequency'], freq, thrs)
            self.assertEqual(risk_allele, 'C?')
            self.assertEqual(notes, 'Snpdb freq for X not found, but Snpdb freq for rev(X) not found')

    def test_allele_strand_check_unsolve(self):
        for thrs in [0.0, 0.1]:
            # C(0.1) vs G(0.9)/A(0.1) => C?
            self.data.update({'risk_allele_frequency': 0.1})
            freq = {'European': {'G': 0.9, 'A': 0.1}}
            risk_allele = get_forward_risk_allele(self.data['risk_allele'], self.data['risk_allele_frequency'], freq, thrs)
            self.assertEqual(risk_allele, 'C?')
            self.assertEqual(notes, 'Snpdb freq for X not found, but not solved with rev(X)')
