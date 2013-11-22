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


## Notice

* Theme

  * [Bootstrap](//getbootstrap.com/), Apache License v2.0
  * Background pattern is downloaded from [subtlepatterns.com](//subtlepatterns.com/), [free to use](//subtlepatterns.com/about/)


* Data visualization

  * Highcharts JS, [for free under the Creative Commons Attribution-NonCommercial 3.0 License](//shop.highsoft.com/highcharts.html)
