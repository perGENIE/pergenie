#!/usr/bin/env bash

# USAGE: ./screenshot/make.sh
# NOTE: Need to be run on django project root.

make node_modules/phantomjs
export PATH=./node_modules/phantomjs/bin:$PATH

. ./.virtualenv/perGENIE/bin/activate
python manage.py runserver 8888 &
python screenshot/create_screenshots.py

kill -TERM -$$
