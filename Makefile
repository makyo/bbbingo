VE ?= venv

run: $(VE)
	$(VE)/bin/python bbbingo.py

$(VE): $(VE)
	virtualenv $(VE)
	$(VE)/bin/pip install -r requirements.txt
