PYTHON=python3
LINTER=flake8

default: all

all: lint test

lint:
	find . -name "*.py" -print | xargs $(LINTER)

test:
	$(PYTHON) -m unittest discover tests/
