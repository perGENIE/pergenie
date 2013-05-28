#!/bin/sh

mysql_root_password=$1

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 MYSQL_ROOT_PASSWORD" >&2
  exit 1
fi

function url() {
    echo http://bioq.saclab.net/query/download_table.php?db=bioq_dbsnp_human_137\&table=${1}\&format=mysql
}


# Download files
for x in Allele AlleleFreqBySsPop b137_ContigInfo b137_SNPContigLoc b137_SNPContigLocusId b137_SNPMapInfo FreqSummaryBySsPop GeneIdToName GtyFreqBySsPop LocTypeCode OrganismTax Pedigree PopLine Population SNP SNPAncestralAllele SnpClassCode SnpFunctionCode SNPSubSNPLink SnpValidationCode SNP_HGVS UniGty UniVariation _loc_allele_freqs _loc_classification_ref _loc_functional_representative _loc_genotype_freqs _loc_maf _loc_sample_information _loc_snp_gene_list_ref _loc_snp_gene_ref _loc_snp_gene_rep_ref _loc_snp_summary _loc_table_log _loc_unique_mappings_ref _loc_validation; \
do url=`url ${x}`; wget -O ${x}.sql.gz ${url}; done

# TODO: create table `bioq_dbsnp_human_137` if not exists.
# TODO: drop if table `bioq_dbsnp_human_137` exists.

# Import into MySQL
for x in *; do echo "Importing: ${x}"; gunzip --to-stdout $x | mysql --user=root --password=$mysql_root_password bioq_dbsnp_human_137; done
