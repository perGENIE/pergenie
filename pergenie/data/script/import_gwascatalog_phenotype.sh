#!/usr/bin/env bash

PG_DB=$1
PG_USER=$2
DATA=$3

psql $PG_DB $PG_USER -q <<EOS
DROP TABLE IF EXISTS GwasCatalogPhenotype;
CREATE TABLE GwasCatalogPhenotype (
    phenotype_en                   varchar  not null,
    phenotype_ja                   varchar,
    category                       varchar,
    sex                            varchar
);
EOS

cat $DATA| psql $PG_DB $PG_USER -c "COPY GwasCatalogPhenotype FROM stdin DELIMITERS '	' WITH NULL AS ''" -q

# Export
psql $PG_DB $PG_USER -c "SELECT DISTINCT disease_or_trait,phenotype_ja,category,sex FROM gwascatalog g LEFT JOIN gwascatalogphenotype p ON g.disease_or_trait = p.phenotype_en ORDER BY disease_or_trait" -A -F$'\t' -X -t
