README
------

* Install perGENIE

    #. See INSTALL.rst


* Test perGENIE

    #. Tests by django::

        $ python manage.py test frontend
        $ python manage.py test


* Launch perGENIE

    #. Launch celeryd::

        $ python manage.py celeryd &


    #. Launch djnago (wsgi or fcgi)::

        $ python manage.py runserver


    #. Access localhost:8000 from browser, then you will see login page.

