===============
perGENIE README
===============

HOW TO USE
----------

* Install perGENIE

    *. See `Installation Guides` bellow.


* Test perGENIE

    *. Tests by django::

        $ python manage.py test frontend dashboard tutorial upload  # ...
        $ python manage.py test


* Import datas

    #. Import GWAS Catalog::

        $ python manage.py import --gwascatalog


* Launch perGENIE

    #. Launch celeryd::

        $ python manage.py celeryd_detach


    #. Launch djnago::

        $ python manage.py runserver


    #. Access localhost:8000 from browser, then you will see login page.

        *. If you get errors,

            *. "python module import error"

                *. Installation via pip may have failed.

            *. "connection refused"

                *. Installation of MongoDB or RabbitMQ failed.

                *. Or launching MongoDB or RabbitMQ failed.


Installation Guides
===================

Getting Started with perGENIE on OS X
-------------------------------------

* Install requirements for perGENIE

    #. Install MongoDB, RabbitMQ via macports::

        $ sudo port install mongodb rabbitmq-server


        $ # Launch mongod
        $ mongod --dbpath=/path/to/elsewhere

        $ # Launch rabbitmq-server
        $ sudo rabbitmqctl start


    #. Install Python libraries via pip::

        $ sudo pip install -r requirements.txt


* Initialize perGENIE

    #. Initialize database (require sqlite3)::

        $ python manage.py syncdb


    #. Initialize celeryd log::

        $ touch log/celeryd.log
