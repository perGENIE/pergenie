usage:
	@echo "USAGE: make [development|clean]"

.virtualenv/perGENIE:
	virtualenv .virtualenv/perGENIE

development: .virtualenv/perGENIE
	. .virtualenv/perGENIE/bin/activate; pip install -r ../requirements/development.txt

#
node_modules/phantomjs:
	npm install phantomjs

clean:
	rm -rf .virtualenv
