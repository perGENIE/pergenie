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
    
        $ mkdir -p log
        $ touch log/celeryd.log


* Launch perGENIE:

    #. Launch celeryd::

        $ python manage.py celeryd &


    #. Launch djnago::

        $ python manage.py runserver


    #. Access localhost:8000 from browser, then you will see login page.

        *. You may get errors, 
        
            *. "python module import error"

                *. Installation via pip may have failed.

            *. "connection refused"

                *. Installation of MongoDB or RabbitMQ failed.

                *. Or launching MongoDB or RabbitMQ failed.
