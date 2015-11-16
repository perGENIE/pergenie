[![perGENIE screenshot](http://knmkr.info/img/portfolio/pergenie.png)](http://pergenie.org/)

## Getting started for development env

1\. Install requirements

- [Python](https://www.python.org/) >=2.7,<3
- [PostgreSQL](http://www.postgresql.org/)
- [RabbitMQ](https://www.rabbitmq.com/)

2\. Install Python packages

```
$ pip install -r requirements/development.txt
```

3\. Configure settings.py

```
$ ${EDITOR} pergenie/settings/development.py  # e.g. pergenie/settings/development.py.example
```

4\. Create PostgreSQL user and database

```
$ createuser pergenie
$ createdb pergenie -O pergenie
```

5\. DB migration

```
$ python manage.py migrate
```

6\. Init data

```
$ python manage.py createsuperuser
$ python manage.py update_gwascatalog
$ python manage.py setup_go_vcf_tools
$ python manage.py init_demo_user
```

7\. Run Celery (for job queing)

```
$ celery --app=pergenie worker --logfile=/tmp/celeryd.log --pidfile=celery%n.pid
```

8\. Run perGENIE server

```
$ python manage.py runserver
```

9\. Browse development server at `http://127.0.0.1:8000/`


## Getting started for staging and production env

See `pergenie/deploy`.


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
