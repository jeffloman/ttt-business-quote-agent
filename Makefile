.PHONY: venv deps web demo cli test

venv:
	python -m venv .venv

deps: venv
	. .venv/bin/activate && pip install -U pip && pip install -r requirements.txt

web: deps
	. .venv/bin/activate && python web_app.py

demo: deps
	. .venv/bin/activate && python demo.py

cli: deps
	. .venv/bin/activate && python app.py

test: deps
	. .venv/bin/activate && python -m unittest -q