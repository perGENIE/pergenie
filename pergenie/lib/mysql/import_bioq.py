import sys, os
import subprocess

def import_bioq(settings):
    tables = ['GeneIdToName']

    # ['Allele', 'AlleleFreqBySsPop', 'b137_ContigInfo', 'b137_SNPContigLoc', 'b137_SNPContigLocusId', 'b137_SNPMapInfo', 'FreqSummaryBySsPop', 'GeneIdToName', 'GtyFreqBySsPop', 'LocTypeCode', 'OrganismTax', 'Pedigree', 'PopLine', 'Population', 'SNP', 'SNPAncestralAllele', 'SnpClassCode', 'SnpFunctionCode', 'SNPSubSNPLink', 'SnpValidationCode', 'SNP_HGVS', 'UniGty', 'UniVariation', '_loc_allele_freqs', '_loc_classification_ref', '_loc_functional_representative', '_loc_genotype_freqs', '_loc_maf', '_loc_sample_information', '_loc_snp_gene_list_ref', '_loc_snp_gene_ref', '_loc_snp_gene_rep_ref', '_loc_snp_summary', '_loc_table_log', '_loc_unique_mappings_ref', '_loc_validation']

    for table in tables:
        print 'importing', table
        sqlfile = os.path.join(settings.BIOQ_DIR, table + '.sql.gz')
        if not os.path.exists(sqlfile): continue
        p1 = subprocess.Popen(["gunzip", "--to-stdout", sqlfile], stdout=subprocess.PIPE)
        p2 = subprocess.Popen(["mysql",
                               "-u", settings.DATABASE['bioq']['USER'],
                               "-p" + settings.DATABASE['bioq']['PASSWORD'],
                               "bioq"],
                              stdin=p1.stdout, stdout=subprocess.PIPE)
        # p1.stdout.close()  # Allow p1 to receive a SIGPIPE if p2 exits.
        output = p2.communicate()[0]
        print output
