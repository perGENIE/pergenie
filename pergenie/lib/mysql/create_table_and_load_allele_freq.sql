-- AFR

-- ASN
DROP TABLE IF EXISTS `ASN_allele_freq`;
CREATE TABLE `ASN_allele_freq` (
  `snp_id` int(11) DEFAULT NULL,
  `unique_chr` varchar(2) DEFAULT NULL,
  `unique_pos_bp` bigint(12) DEFAULT NULL,
  `alt_1` char(1) NOT NULL,
  `alt_2` char(1) NOT NULL,
  `freq_alt_1` float NOT NULL,
  `freq_alt_2` float NOT NULL,
  KEY `i_snp_id` (`snp_id`),
  KEY `i_chr_pos` (`unique_chr`,`unique_pos_bp`)
 );

LOAD DATA INFILE "/Volumes/Macintosh HD 2/reference/pergenie/umich_1kg_freq/ASN/ASN_allele_freq.csv" INTO TABLE `ASN_allele_freq` FIELDS TERMINATED BY ',';

-- EUR
