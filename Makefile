PYTHON=python3
LINTER=flake8

default: all

all: lint test

# Fail if there any TODOs left in the source code.
todos:
	! find . -name "*.py" -print | xargs grep -e "TODO"

lint:
	find . -name "*.py" -print | xargs $(LINTER)

test:
	$(PYTHON) -m unittest discover tests/
