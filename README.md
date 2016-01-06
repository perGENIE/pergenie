[![perGENIE screenshot](http://knmkr.info/img/portfolio/pergenie/pergenie.png)](http://pergenie.org/)

## For developers

### Getting started with Vagrant & Ansible

1\. Install `VirtualBox`, `Vagrant`, and `Ansible`.

2\. Configure variables in playbook:

```
$ ${EDITOR} pergenie/deploy/playbook/group_vars/staging  # e.g. pergenie/deploy/playbook/group_vars/example/staging.example
```

3\. Build VM and deploy:

```
$ cd pergenie/deploy
$ vagrant up
```

Once VM is up, you can rollout pergenie application by:

```
$ ANSIBLE_TAGS=rollout vagrant provision
```

See details in `pergenie/deploy`


### Getting started with Django development server

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
$ createuser pergenie --password
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

7\. Run Celery for job queing

```
$ DJANGO_SETTINGS_MODULE=pergenie.settings.development celery --app=pergenie worker
```

8\. Run development server

```
$ python manage.py runserver
```

9\. Browse application at `http://127.0.0.1:8000/`


## Notice

### About public data resources

Versions of public data resources are pinned as follows:

| Resources              | Versions         |
|------------------------|------------------|
| Human Reference Genome | GRCh37p13        |
| dbSNP                  | b144             |


### About html design data

- Currently, main design data (`static/vendor/wood-admin/stylesheets/application.css`) is not included in this repository. You can purchase from [wrapbootstrap.com/theme/wood-admin-theme-WB0941911](//wrapbootstrap.com/theme/wood-admin-theme-WB0941911). Sorry for inconvenience.

- Following open source stylesheet/image/javascript products are used under the each license:
  - [Bootstrap](//getbootstrap.com/), Apache License v2.0
  - [Highcharts JS](//www.highcharts.com/), [for free under the Creative Commons Attribution-NonCommercial 3.0 License](//shop.highsoft.com/highcharts.html)
  - [jQuery](//jquery.com/), MIT License
  - [jQuery MultiFile](//www.fyneworks.com/jquery/multifile/), MIT License
  - [Peity](//benpickles.github.io/peity/), MIT License
  - [Intro.js](//usablica.github.io/intro.js/), MIT License
  - [google/code-prettify](//github.com/google/code-prettify/), Apache License v2.0


## License

See `LICENSE`
