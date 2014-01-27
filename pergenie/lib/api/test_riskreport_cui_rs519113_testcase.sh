#!/usr/bin/env bash

mkdir tmp

# normal & without rs ID
for zyg in CC CG GG NA; do \
    for src in .vcf _without_rsID.vcf; do \
        echo $zyg $src
        $WORKON_HOME/py26perGENIE/bin/python \
         riskreport_cui.py \
         -I rs519113_testcase/rs519113_${zyg}${src} \
         -F vcf_whole_genome \
         -O tmp/${zyg}.out \
         -P Asian
        grep Alz tmp/$zyg.out > tmp/$zyg.Alz.out
        diff tmp/$zyg.Alz.out rs519113_testcase/true_outputs/$zyg.Alz.out
    done
done

# gzipped
for zyg in CC CG GG NA; do \
    for src in .vcf.gz; do \
        echo $zyg $src
        $WORKON_HOME/py26perGENIE/bin/python \
         riskreport_cui.py \
         -I rs519113_testcase/rs519113_${zyg}${src} \
         -F vcf_whole_genome \
         -O tmp/${zyg}.out \
         -P Asian \
         --compress gzip
        grep Alz tmp/$zyg.out > tmp/$zyg.Alz.out
        diff tmp/$zyg.Alz.out rs519113_testcase/true_outputs/$zyg.Alz.out
    done
done

# rm -r tmp
