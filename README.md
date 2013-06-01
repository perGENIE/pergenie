#perGENIE

##Installation

###Getting Started with perGENIE on OS X

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
$ vi pergenie/pergenie/settings/develop.py
```

3\. Initialize

```
# Initialize database
$ python manage.py syncdb
$ python manage.py import --gwascatalog
$ python manage.py import --demodata

#
$ mkdir -p /tmp/uploaded
$ chmod 777 /tmp/uploaded
```

4\. Tests

```
#
```

5\. Run

```
$ python manage.py celeryd_detach
$ python manage.py runserver 8080
```
