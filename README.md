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
