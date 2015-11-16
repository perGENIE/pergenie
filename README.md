[![perGENIE screenshot](http://knmkr.info/img/portfolio/pergenie.png)](http://pergenie.org/)

## Getting started

### with Django development server

1\. Install requirements

- [Python](https://www.python.org/) >=2.7,<3
- [PostgreSQL](http://www.postgresql.org/)
- [RabbitMQ](https://www.rabbitmq.com/)
- Python packages
  - Run `$ pip install -r requirements/development.txt`
- Command-line vcf tools
  - Download binaries from https://github.com/knmkr/go-vcf-tools/releases/download/${version}, and put them at `pergenie/bin`
- Merge history of rs IDs
  - Download from `ftp.ncbi.nih.gov/snp/organisms/human_9606_b144_GRCh37p13/database/organism_data/RsMergeArch.bcp.gz` and put at `RS_MERGE_ARCH_PATH`

2\. Configure settings.py

```
$ ${EDITOR} pergenie/settings/develop.py  # e.g. pergenie/settings/develop.py.example
```

3\. Create postgres user and database

```
$ createuser pergenie
$ createdb pergenie -O pergenie
```

4\. Database migration

```
$ python manage.py migrate
```

5\. Init data

```
$ python manage.py createsuperuser
$ python manage.py update_gwascatalog
$ python manage.py init_demo_user
```

6\. Run celery

```
$ celery --app=pergenie worker --logfile=/tmp/celeryd.log --pidfile=celery%n.pid
```

7\. Run pergenie server

```
$ python manage.py runserver
```

Browse development server at `http://127.0.0.1:8000/`


## Notes

- Versions of public database sources are fixed as following:

| source                 | version          |
|------------------------|------------------|
| Human Reference Genome | GRCh37p13        |
| dbSNP                  | b144             |


## Notice

* Theme

  * [Bootstrap](//getbootstrap.com/), Apache License v2.0

* Data visualization

  * Highcharts JS, [for free under the Creative Commons Attribution-NonCommercial 3.0 License](//shop.highsoft.com/highcharts.html)


## License

See `LICENSE`
