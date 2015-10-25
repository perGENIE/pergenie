[![perGENIE screenshot](http://knmkr.info/img/portfolio/pergenie.png)](http://pergenie.org/)

## Getting started

### with Django development server

1\. Install requirements

- [Python]() >=2.7,<3
- [PostgreSQL]()
- [RabbitMQ]()

- Python packages:

```
$ pip install -r requirements/development.txt
```

- Command-line vcf tools
  - Download binaries from https://github.com/knmkr/go-vcf-tools/releases/download/${version}, and put them at `pergenie/bin`


2\. Configure environments settings

```
$ cp pergenie/settings/common.py.example pergenie/settings/common.py
$ cp pergenie/settings/develop.py.example pergenie/settings/develop.py
```

3\. Preparing backends

- Run postgres server

- Run database migration

```
$ python manage.py migrate
```

- Run rabbitmq-server

- Run celery

as daemon

```
$ celery multi start 1 --app=pergenie --loglevel=info --logfile=/tmp/celeryd.log --pidfile=celery%n.pid
$ celery multi restart 1 --logfile=/tmp/celeryd.log --pidfile=celery%n.pid
```

or run in foreground (for development only)

```
$ celery --app=pergenie worker --logfile=/tmp/celeryd.log --pidfile=celery%n.pid
```

- [optional] Create super-user to login

```
$ python manage.py createsuperuser
```

4\. Run

Run local server (for development only)

```
$ python manage.py runserver
```

Browse development server at `http://127.0.0.1:8000/`


## Notice

* Theme

  * [Bootstrap](//getbootstrap.com/), Apache License v2.0

* Data visualization

  * Highcharts JS, [for free under the Creative Commons Attribution-NonCommercial 3.0 License](//shop.highsoft.com/highcharts.html)


## License

See `LICENSE`
