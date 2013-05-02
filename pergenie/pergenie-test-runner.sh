#!/bin/sh
notifier=/opt/local/bin/terminal-notifier

# python virtualenv
. /Users/numa/.virtualenvs/perGENIE/bin/activate

# main
cd /Users/numa/Dropbox/py/pergenie_staging/pergenie
python manage.py celeryd_detach

for app in frontend dashboard upload riskreport traits library faq
do
  python manage.py test $app

  # Test Failed:
  if [ $? -eq 1 ]; then
    $notifier -message "pergenie-test-runner.sh: Test Failed: ${app}"
  fi

done
