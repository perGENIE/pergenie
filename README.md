### Getting Started on OS X

1\. Install requirements

```
# MongoDB
$ sudo port install mongodb
$ sudo port load mongodb

# RabbitMQ
$ sudo port install rabbitmq-server
$ sudo port load rabbitmq-server

# Python modules
$ sudo pip install -r requirements.txt
```

2\. Settings

```
$ ${EDITOR} pergenie/pergenie/settings/develop.py
```

3\. Initialize

```
# FIXME
```

4\. Tests

```
# FIXME
```

5\. Run

```
$ python manage.py celeryd_detach
$ python manage.py runserver 8080
```


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



## Web-documentation

[perGENIE documentation]() is built by [Sphinx - Python documentation generator](//sphinx-doc.org/).


To build documentation locally, install `omake` and run

   omake -P --verbose

in `perGENIE/web-documentation` directory.


## Notice

* Theme

  * [Bootstrap](//getbootstrap.com/), Apache License v2.0
  * Background pattern is downloaded from [subtlepatterns.com](//subtlepatterns.com/), [free to use](//subtlepatterns.com/about/)


* Data visualization

  * Highcharts JS, [for free under the Creative Commons Attribution-NonCommercial 3.0 License](//shop.highsoft.com/highcharts.html)
