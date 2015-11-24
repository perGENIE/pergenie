# GwasCatalog

## manage.py commands

Update GWAS Catalog records for risk report

```
$ python manage.py update_gwascatalog
```

- Fetch and cleanup GWAS Catalog data, and store as apps.gwascatalog.models.GwasCatalogSnp and apps.gwascatalog.models.GwasCatalogPhenotype.
- Fetch allele frequency data for SNPs in GWAS Catalog, and store as apps.snp.models.Snp.
