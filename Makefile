VE ?= venv

.PHONY: run
run: $(VE)
	FLASK_APP=bbbingo.py $(VE)/bin/flask run --host=0.0.0.0 --reload --debugger

.PHONY: check
check: lint test

.PHONY: lint
lint: $(VE)
	$(VE)/bin/flake8 *.py

.PHONY: test
test: $(VE)
	$(VE)/bin/nosetests

$(VE):
	virtualenv $(VE)
	$(VE)/bin/pip install -r requirements.txt
