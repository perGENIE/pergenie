import sys, os
import subprocess
from django.conf import settings
from utils import clogging
log = clogging.getColorLogger(__name__)


def import_bioq(settings):
    # tables = ['Allele', 'AlleleFreqBySsPop', 'b137_ContigInfo', 'b137_SNPContigLoc', 'b137_SNPContigLocusId', 'b137_SNPMapInfo', 'FreqSummaryBySsPop', 'GeneIdToName', 'GtyFreqBySsPop', 'LocTypeCode', 'OrganismTax', 'Pedigree', 'PopLine', 'Population', 'SNP', 'SNPAncestralAllele', 'SnpClassCode', 'SnpFunctionCode', 'SNPSubSNPLink', 'SnpValidationCode', 'SNP_HGVS', 'UniGty', 'UniVariation', '_loc_allele_freqs', '_loc_classification_ref', '_loc_functional_representative', '_loc_genotype_freqs', '_loc_maf', '_loc_sample_information', '_loc_snp_gene_list_ref', '_loc_snp_gene_ref', '_loc_snp_gene_rep_ref', '_loc_snp_summary', '_loc_table_log', '_loc_unique_mappings_ref', '_loc_validation']

    mintables = ['_loc_allele_freqs', '_loc_snp_summary', 'b137_SNPContigLoc', 'GeneIdToName']
    tables = mintables

    for table in tables:
        sqlfile = os.path.join(settings.BIOQ_DIR, table + '.sql.gz')
        if not os.path.exists(sqlfile):
            log.info('Fetching %s' % table)
            url = 'http://bioq.saclab.net/query/download_table.php?db=bioq_dbsnp_human_137&table={0}&format=mysql'.format(table)
            p0 = subprocess.Popen(["wget", "--no-check-certificate", "-O", sqlfile, url])
            log.info('Status %s' % p0.communicate()[0])

        log.info('Importing %s' % table)
        p1 = subprocess.Popen(["gunzip", "--to-stdout", sqlfile], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["mysql",
                               "-u", settings.DATABASES['bioq']['USER'],
                               "--password=" + settings.DATABASES['bioq']['PASSWORD'],
                               settings.DATABASES['bioq']['NAME']],
                              stdin=p1.stdout, stdout=subprocess.PIPE)
        p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
        log.info('Status %s' % p2.communicate()[0])
