#!/usr/bin/env python

import sys,os
import socket
import unittest
sys.path.append('../')
host = socket.gethostname()
if host.endswith('.local'):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pergenie.settings.develop")
else:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pergenie.settings.staging")

from import_catalog import _risk_allele


class bq(object):
    """
    mock of BioQ
    """

    def __init__(self, freqs):
        self.freqs = freqs

    def get_allele_freqs(self, rs):
        return self.freqs, None


class SimpleTest(unittest.TestCase):
    def setUp(self):
        self.data = {'strongest_snp_risk_allele': 'rs3-C',
                     'risk_allele_frequency': 0.1,
                     'population': ['European']}

    def test_allele_strand_check_ok(self):
        """
        Note:
        It is odd if risk allele freq is equal to other allele. However, we accept as they are.
        """

        for thrs in [0.0, 0.1]:
            # C(0.1) vs C(0.1)/T(0.9) => C
            self.data.update({'risk_allele_frequency': 0.1})
            bioq = bq(freqs={'European': {'C': {'freq': 0.1}, 'T': {'freq': 0.9}}})
            rs, risk_allele, notes = _risk_allele(self.data, thrs=thrs, bioq=bioq)
            self.assertEqual(risk_allele, 'C')
            self.assertEqual(notes, 'ok')

            # C(0.5) vs C(0.5)/T(0.5) => C
            self.data.update({'risk_allele_frequency': 0.5})
            bioq = bq(freqs={'European': {'C': {'freq': 0.5}, 'T': {'freq': 0.5}}})
            rs, risk_allele, notes = _risk_allele(self.data, thrs=thrs, bioq=bioq)
            self.assertEqual(risk_allele, 'C')
            self.assertEqual(notes, 'ok')

            # C(0.9) vs C(0.9)/T(0.1) => C
            self.data.update({'risk_allele_frequency': 0.9})
            bioq = bq(freqs={'European': {'C': {'freq': 0.9}, 'T': {'freq': 0.1}}})
            rs, risk_allele, notes = _risk_allele(self.data, thrs=thrs, bioq=bioq)
            self.assertEqual(risk_allele, 'C')
            self.assertEqual(notes, 'ok')

            # C(0.5) vs G(0.5)/C(0.5) => C
            self.data.update({'risk_allele_frequency': 0.5})
            bioq = bq(freqs={'European': {'G': {'freq': 0.5}, 'C': {'freq': 0.5}}})
            rs, risk_allele, notes = _risk_allele(self.data, thrs=thrs, bioq=bioq)
            self.assertEqual(risk_allele, 'C')
            self.assertEqual(notes, 'ok')

    def test_allele_strand_check_solved(self):
        for thrs in [0.0, 0.1]:
            # C(0.1) vs G(0.1)/A(0.9) => G
            self.data.update({'risk_allele_frequency': 0.1})
            bioq = bq(freqs={'European': {'G': {'freq': 0.1}, 'A': {'freq': 0.9}}})
            rs, risk_allele, notes = _risk_allele(self.data, thrs=thrs, bioq=bioq)
            self.assertEqual(risk_allele, 'G')
            self.assertEqual(notes, 'BioQ freq for X not found, and solved with rev(X)')

            # C(0.5) vs G(0.5)/A(0.5) => G
            self.data.update({'risk_allele_frequency': 0.5})
            bioq = bq(freqs={'European': {'G': {'freq': 0.5}, 'A': {'freq': 0.5}}})
            rs, risk_allele, notes = _risk_allele(self.data, thrs=thrs, bioq=bioq)
            self.assertEqual(risk_allele, 'G')
            self.assertEqual(notes, 'BioQ freq for X not found, and solved with rev(X)')

            # C(0.9) vs G(0.9)/A(0.1) => G
            self.data.update({'risk_allele_frequency': 0.9})
            bioq = bq(freqs={'European': {'G': {'freq': 0.9}, 'A': {'freq': 0.1}}})
            rs, risk_allele, notes = _risk_allele(self.data, thrs=thrs, bioq=bioq)
            self.assertEqual(risk_allele, 'G')
            self.assertEqual(notes, 'BioQ freq for X not found, and solved with rev(X)')

            # C(0.1) vs G(0.1)/C(0.9) => G
            self.data.update({'risk_allele_frequency': 0.1})
            bioq = bq(freqs={'European': {'G': {'freq': 0.1}, 'C': {'freq': 0.9}}})
            rs, risk_allele, notes = _risk_allele(self.data, thrs=thrs, bioq=bioq)
            self.assertEqual(risk_allele, 'G')
            self.assertEqual(notes, 'Inconsistence between GWAS Catalog and BioQ, and solved with rev(X)')

            # C(0.9) vs G(0.9)/C(0.1) => G
            self.data.update({'risk_allele_frequency': 0.9})
            bioq = bq(freqs={'European': {'G': {'freq': 0.9}, 'C': {'freq': 0.1}}})
            rs, risk_allele, notes = _risk_allele(self.data, thrs=thrs, bioq=bioq)
            self.assertEqual(risk_allele, 'G')
            self.assertEqual(notes, 'Inconsistence between GWAS Catalog and BioQ, and solved with rev(X)')

    def test_allele_strand_check_unsolve_absence_of_freq_in_dbsnp(self):
        for thrs in [0.0, 0.1]:
            # C vs T/A => C?
            self.data.update({'risk_allele_frequency': 0.1})
            bioq = bq(freqs={'European': {'T': {'freq': 0.1}, 'A': {'freq': 0.9}}})
            rs, risk_allele, notes = _risk_allele(self.data, thrs=thrs, bioq=bioq)
            self.assertEqual(risk_allele, 'C?')
            self.assertEqual(notes, 'BioQ freq for X not found, but BioQ freq for rev(X) not found')

    def test_allele_strand_check_unsolve(self):
        for thrs in [0.0, 0.1]:
            # C(0.1) vs G(0.9)/A(0.1) => C?
            self.data.update({'risk_allele_frequency': 0.1})
            bioq = bq(freqs={'European': {'G': {'freq': 0.9}, 'A': {'freq': 0.1}}})
            rs, risk_allele, notes = _risk_allele(self.data, thrs=thrs, bioq=bioq)
            self.assertEqual(risk_allele, 'C?')
            self.assertEqual(notes, 'BioQ freq for X not found, but not solved with rev(X)')


if __name__ == '__main__':
    unittest.main()
