#perGENIE

##Installation

###Getting Started with perGENIE on OS X

1. Install requirements

```
# MongoDB
$ sudo port install mongodb
$ mongod --dbpath=/path/to/elsewhere

# RabbitMQ
$ sudo port install rabbitmq-server
$ sudo rabbitmqctl start

# Python modules
$ sudo pip install -r requirements.txt
```

2. Settings

```
# Fill setings
$ vi ./pergenie/settings/develop.py
```

3. Initialize

```
# Initialize database
$ python manage.py syncdb
$ python manage.py import --gwascatalog
$ python manage.py import --demodata

#
$ mkdir -p /tmp/uploaded
$ chmod 777 /tmp/uploaded
```

4. Tests

```
#
```

5. Run

```
$ python manage.py celeryd_detach
$ python manage.py runserver 8080
```
