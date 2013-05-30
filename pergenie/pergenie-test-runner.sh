#!/bin/sh

notifier=/opt/local/bin/terminal-notifier
# . /Users/numa/.virtualenvs/perGENIE/bin/activate  # py27
. /Users/numa/.virtualenvs/py26perGENIE/bin/activate  # py26

which python
which nosetests

cd /Users/numa/Dropbox/py/pergenie/pergenie/
python manage.py celeryd_detach

# tests for app
for app in frontend dashboard upload riskreport traits library faq
do
  python manage.py test $app

  # Test Failed:
  if [ $? -eq 1 ]; then
    $notifier -message "pergenie-test-runner.sh: Test Failed: ${app}"
  fi
done

# tests for lib
cd lib/
nosetests -v --with-doctest --doctest-extension=.txt
if [ $? -eq 1 ]; then
    $notifier -message "pergenie-test-runner.sh: Test Failed: nosetests"
fi
