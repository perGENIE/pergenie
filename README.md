### Getting started with development server

1\. Install requirements

- [Python]() >=2.7,<3
- [PostgreSQL]()
- [MongoDB]()
- [RabbitMQ]()
- Python packages:

```
$ pip install -r requirements/development.txt
```

2\. Configure environments settings

```
$ cp pergenie/pergenie/settings/common.py.example pergenie/pergenie/settings/common.py
$ cp pergenie/pergenie/settings/develop.py.example pergenie/pergenie/settings/develop.py
```

3\. Preparing backends

- Run postgres
- Run mongod
- Run rabbitmq-server

```
$ cd pergenie
$ python manage.py migrate
```

```
$ celery multi start 1 --app=pergenie --loglevel=info --logfile=/tmp/celeryd.log --pidfile=celery%n.pid
$ celery multi restart 1 --logfile=/tmp/celeryd.log --pidfile=celery%n.pid
```

4\. Run

```
$ python manage.py runserver
```

Browse development server at `http://127.0.0.1:8000/`


## CUI

### Batch-import

To batch-import genome files,

   1. Place genome files as `/path_to_genome_file_dir/file_format/genome_file`.
      For example,

      $ ls ~/knmkr/genomes/vcf_whole_genome
      genome1.vcf genome2.vcf genome3.vcf

   2. Set `user_id` and path to genome file directory in Django settings.
      For example, in pergenie/settings/develop.py,

      CRON_DIRS = {'knmkr@pergenie.org': ['~/knmkr/genomes']}

   3. Run batch-import command

      $ manage.py import --genomes


### Delete genome data

To delete genome data (data_info in DB, user_id.variants in DB, and genome file), run following command with user_id

   $ lib/mongo/utils/mongo_variants_utils.py --drop user_id


### Risk Report

To get risk report (.csv),

1. Set up GWAS Catalog data. (Generate portable version of GWAS Catalog records)

   $ ../../manage.py export --gwascatalog

2. Then, calculate risk estimation.

   $ lib/api/riskreport_cui.py \
   -I DRA000583.vcf \
   -F vcf_whole_genome \
   -O DRA000583.csv \
   -P Japanese


## Web-documentation

[perGENIE documentation]() is built by [Sphinx - Python documentation generator](//sphinx-doc.org/).


To build documentation locally, install `omake` and run

   omake -P --verbose

in `perGENIE/web-documentation` directory.


### Export GWAS Catalog

To export GWAS Catalog records,

    $ python manage.py export --gwascatalog

then, pickled files for each population `gwascatalog.pergenie.{#population}.p` will be generated.


## Notice

* Theme

  * [Bootstrap](//getbootstrap.com/), Apache License v2.0
  * Background pattern is downloaded from [subtlepatterns.com](//subtlepatterns.com/), [free to use](//subtlepatterns.com/about/)


* Data visualization

  * Highcharts JS, [for free under the Creative Commons Attribution-NonCommercial 3.0 License](//shop.highsoft.com/highcharts.html)
